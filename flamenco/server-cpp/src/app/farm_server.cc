// Copyright (c) 2015 farm-proto authors.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to
// deal in the Software without restriction, including without limitation the
// rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
// sell copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
// IN THE SOFTWARE.

#include <cstdlib>
#include <csignal>
#include <getopt.h>
#include <fstream>

#include "http/http_server_soup.h"
#include "model/model_farm.h"
#include "storage/storage_dryrun.h"
#include "storage/storage_database_sqlite.h"
#include "util/util_config.h"
#include "util/util_function.h"
#include "util/util_string.h"
#include "util/util_logging.h"
#include "util/util_time.h"

/* Use dry-run (emory-only, no serialization) storage. */
// #define DRY_RUN_STORAGE
/* Create full bunch of new jobs, for development purposes only. */
#define CREATE_NEW_JOBS
/* Count of new tasks to be created. */
#define NEW_TASKS_COUNT 4

namespace Farm {

namespace {

Farm *farm = NULL;
HTTPServer *http_server = NULL;
Storage *storage = NULL;

void signal_quit(int sig) {
  VLOG(1) << "Performing shutdown sequence...";
  http_server->stop_serve();
}

}  /* namespace */

int main(int argc, char **argv) {
  /* Set default configuration values for the application. These values can be
   overridden using a config file (by default server.config, next to the
   binary). Alternatively, values can be passed as command line arguments. In
   this case, they will override any default value, as well as config file. */
  int log_level = 0;
  string config_database_path_value = "/tmp/farm.sqlite";
  string config_storage_path_value = "/tmp";
  string dry_run_storage_value = "false";
  string config_config_path_value = "server.config";
  int port = 9999;

  int c;
  while (1) {
    int option_index = 0;
    static struct option long_options[] = {
      {"debug",    no_argument,       0, 'd'},
      {"loglevel", required_argument, 0, 'v'},
      {"config",   required_argument, 0, 'c'},
      {"dbpath",   required_argument, 0, 'b'},
      {"stpath",   required_argument, 0, 's'},
      {"port",     required_argument, 0, 'p'},
      {0,          0,                 0,  0 }
    };

    c = getopt_long(argc, argv, "dv:bsp:", long_options, &option_index);
    if (c == -1) {
      break;
    }

    switch (c) {
      case 'b':
        config_database_path_value = optarg;
        break;
      case 'v':
        log_level = atoi(optarg);
        break;
      case 'c':
        config_config_path_value = optarg;
        break;
      case 's':
        config_storage_path_value = optarg;
        break;
      case 'p':
        port = atoi(optarg);
        break;
      default:
        printf("Unknown argument with character code 0%o ??\n", c);
    }
  }

  /* Here we load and parse the configuration file, obtaining a map. */
  config server_config(config_config_path_value);

  string config_dry_run_storage = server_config.get_value("dry_run_storage",
                                                          dry_run_storage_value);
  string config_database_path = server_config.get_value("database_path",
                                                        config_database_path_value);
  string config_storage_path = server_config.get_value("storage_path",
                                                       config_storage_path_value);

  signal(SIGINT, signal_quit);

  /* Startup logging utilities. */
  util_logging_init(argv[0]);
  util_logging_start();
  util_logging_verbosity_set(log_level);

  if (config_dry_run_storage == "true") {
    storage = new DryRunStorage(true);
    storage->connect();
  } else {
    // SQLiteStorage *sqlite_storage = new SQLiteStorage(":memory:");
    SQLiteStorage *sqlite_storage = new SQLiteStorage(config_database_path);
    sqlite_storage->connect();
    sqlite_storage->create_schema();

    sqlite_storage->use_bulked_transactions = true;
    sqlite_storage->transaction_commit_interval = 2.0;

    storage = sqlite_storage;
  }

  double start_time = util_time_dt();
  farm = new Farm(storage);
  farm->restore();
#ifdef CREATE_NEW_JOBS
  for(int i = 0; i < NEW_TASKS_COUNT; ++i) {
    farm->insert_job(50,
                     Job::STATUS_WAITING,
                     string_printf("Test Job %d", i));
  }
#endif
  VLOG(1) << "Restored in " << util_time_dt() - start_time << " seconds.";

  http_server = new SOUPHTTPServer(farm,
                                   port,
                                   config_storage_path);
  http_server->idle_function_cb = function_bind(&Farm::idle_handler, farm);
  http_server->start_serve();

  farm->store();
  storage->disconnect();
  delete http_server;
  delete storage;
  delete farm;
  VLOG(1) << "Shutdown sequence completed.";

  return EXIT_SUCCESS;
}

}  /* namespace Farm */

int main(int argc, char **argv) {
  return Farm::main(argc, argv);
}
