const {execSync} = require('child_process');
const {env} = process;
const curlOpts = '--silent --fail --show-error'

const milestone = getMilestone();

const milestoneText = () => {
    let checkbox = "[ ]";
    let note = `⚠️ Could not find milestone matching \`${env.VERSION}\``;
    if (milestone) {
        if (parseInt(milestone.open_issues) === 0) {
            checkbox = "[x]";
        }
        note = `ℹ️ ${milestone.open_issues} other open issues/PRs on [milestone ${milestone.title}](https://github.com/${env.REPOSITORY}/milestone/${milestone.number}) at time of PR creation`;
    }
    return `${checkbox} Milestone complete?\n  ${note}`;
};

const bodyText = `
### ⚡ Merging this PR will automatically create a GitHub Release ⚡

This PR was created by the \`${env.WORKFLOW}\` workflow, triggered by @${env.AUTHOR}

#### Tests:
✔️ \`setup.py\` bdist build test
✔️ Version number valid for PyPI.org

#### Checklist:
- ${milestoneText()}

- [ ] Changelog up-to-date?
  Examine pull requests made since the last release
  "Released on" date updated? ${env.CHANGELOG_DATE ? `✔️ \`${env.CHANGELOG_DATE}\`` : `⚠️ couldn't automatically set date`}

- [ ] All contributors listed?

- [ ] \`.mailmap\` file correct?
  In particular, check for duplication

#### Next steps:
- @${env.AUTHOR} should request 1 or 2 reviews
- If any further changes are needed, push to this PR branch
- After merging, the bot will comment below with a link to the release (if not, look at the PR checks tab)
`;

const payload = JSON.stringify({
    title: `Prepare release: ${env.VERSION}`,
    head: env.HEAD_REF,
    base: env.BASE_REF,
    body: bodyText
});

const request = `curl -X POST \
    https://api.github.com/repos/${env.REPOSITORY}/pulls \
    -H "authorization: Bearer $GITHUB_TOKEN" \
    -H "content-type: application/json" \
    --data '${payload}' \
    ${curlOpts}`;
    // Don't use env.GITHUB_TOKEN above as that might print in log.

const pr = JSON.parse(exec(request));
setMilestoneAndAssignee(pr.number);



function getMilestone() {
    const request = `curl -X GET \
        https://api.github.com/repos/${env.REPOSITORY}/milestones \
        -H "authorization: Bearer $GITHUB_TOKEN" \
        ${curlOpts}`;

    let response;
    try {
        response = JSON.parse(exec(request));
    } catch (err) {
        console.log(`::warning:: Error getting milestones`);
        console.log(err, '\n');
        return;
    }
    for (const milestone of response) {
        if (milestone.title.includes(env.VERSION)) {
            console.log('Found milestone:', milestone.title, '\n');
            return milestone;
        }
    }
    console.log(`::warning:: Could not find milestone matching "${env.VERSION}"`);
    return;
}

function setMilestoneAndAssignee(prNumber) {
    // Cannot set them when creating the PR unfortunately
    const payload = JSON.stringify({
        milestone: milestone ? milestone.number : undefined,
        assignees: [env.AUTHOR]
    });

    const request = `curl -X PATCH \
        https://api.github.com/repos/${env.REPOSITORY}/issues/${prNumber} \
        -H "authorization: Bearer $GITHUB_TOKEN" \
        -H "content-type: application/json" \
        --data '${payload}' \
        ${curlOpts}`;

    exec(request);
}

function exec(cmd) {
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
    console.log(stdout);
    console.log('::endgroup::');
    return stdout;
}
