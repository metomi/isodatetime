const {execSync, curlOpts} = require('./util');
const {env} = process;
const pr_event = JSON.parse(env.PR_EVENT);

const nextSteps = `
Next step for @${pr_event.assignees[0].login}: [view/edit the GitHub release description](${env.RELEASE_URL}) as appropriate
`;

const manualInstructions = `
[Check the run](${pr_event.html_url}/checks)

If you need to publish the dist to PyPI manually:

(Make sure you have commit \`${env.MERGE_SHA}\` checked out)
\`\`\`shell
# Create the build
python3 setup.py bdist_wheel sdist
# Upload your build to PyPI
twine upload dist/*
\`\`\`
`;

const footer = `
___
Comment created by workflow: \`${env.WORKFLOW}\`, run: \`${env.RUN_NUMBER}\`
`;

const bodyText = () => {
    let icon = '✔️';
    let content = nextSteps;
    if (env.JOB_STATUS !== 'success') {
        icon = '❌';
        content = manualInstructions;
    }
    const title = `### ${icon} \`${env.JOB_STATUS}\` \n`;
    return [title, content, footer].join('');
};

const payload = JSON.stringify({
    body: bodyText()
});

execSync(`curl -X POST \
    ${pr_event.comments_url} \
    -H "authorization: Bearer $GITHUB_TOKEN" \
    -H "content-type: application/json" \
    --data '${payload}' \
    ${curlOpts}`
);
