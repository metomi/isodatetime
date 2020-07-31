/* THIS FILE IS PART OF THE CYLC SUITE ENGINE.
Copyright (C) NIWA & British Crown (Met Office) & Contributors.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>. */

// Helper functions for NodeJS steps in GitHub Actions

const {execSync} = require('child_process');

exports.curlOpts = '--silent --fail --show-error';

exports.stringify = (obj) => {
    // JSON.stringify() but escapes single quotes as HTML chars
    return JSON.stringify(obj).replace(/'/g, "&apos;");
}

exports.execSync = (cmd) => {
    // Node's execSync() but with improved logging
    let stdout;
    try {
        stdout = execSync(cmd, {stdio: 'pipe', encoding: 'utf8'});
    } catch (err) {
        console.log(`::error:: ${err.stderr ? err.stderr : 'Error executing command'}`);
        throw err.message;
    }
    console.log(`::group::exec ${cmd.slice(0, 15)}...`);
    console.log('=====================  cmd  ======================');
    console.log(cmd);
    console.log('===================== stdout =====================');
    try {
        console.log(JSON.stringify(JSON.parse(stdout), null, 2));
    } catch {
        console.log(stdout);
    }
    console.log('::endgroup::');
    return stdout;
};
