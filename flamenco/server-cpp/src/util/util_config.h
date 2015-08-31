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

#ifndef UTIL_CONFIG_H_
#define UTIL_CONFIG_H_

#include "util/util_string.h"
#include "util/util_map.h"

namespace Farm {

class config {
 public:
  /* TODO(sergey): Support some more flexible value type. */
  typedef string value_type;

  /* Configuration file constructors */
  config();
  explicit config(const string& file_name);

  /* Check whether specified key is specified in the configuration. */
  bool has_value(const string& key);

  /* Get value corresponding to a specified key.
   * default_value will be returned if the key does not exist in the
   * configuration.
   */
  value_type get_value(const string& key, value_type default_value = "");

  /* Set value for a speficied key. If the key already exists, we update the
   existing value. If it does not exist, we append the pair to the map. */
  value_type set_value(const string& key, value_type value);

 protected:
  bool parse_file(const string& file_name);

  map<string, value_type> values_;
};

}  /* namespace Farm */

#endif /* UTIL_CONFIG_H_ */
