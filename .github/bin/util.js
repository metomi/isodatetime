// Helper functions for NodeJS steps in GitHub Actions

const {execSync} = require('child_process');

exports.curlOpts = '--silent --fail --show-error';

exports.execSync = (cmd) => {
    // Node's execSync but with improved logging
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
