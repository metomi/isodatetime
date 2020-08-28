/* THIS FILE IS PART OF THE CYLC SUITE ENGINE.
Copyright (C) British Crown (Met Office) & Contributors.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>. */

// Comment on PR, close milestone if attached, and update PR title on failure

const {execSync, stringify, curlOpts} = require('./util');
const {env} = process;
const pr_event = JSON.parse(env.PR_EVENT);

let isMilestoneClosed;
if (env.JOB_STATUS === 'success') {
    isMilestoneClosed = closeMilestone();
} else {
    updatePRTitle();
}

const nextSteps = `
Next steps for @${pr_event.assignees[0].login}:
- [view/edit the GitHub release description](${env.RELEASE_URL}) as appropriate
- ${isMilestoneClosed ? '✔️ Milestone automatically closed' : 'Close the milestone'}
- Announce on Element, Discourse, Yammer etc?
`;

const manualInstructions = `
[Check the run](${pr_event.html_url}/checks)

You can still publish the dist to PyPI manually:

(Make sure you have commit \`${env.MERGE_SHA}\` checked out)
\`\`\`shell
# Create the build
python3 setup.py bdist_wheel sdist
# Upload your build to PyPI
twine upload dist/*
\`\`\`

Then [create a GitHub release](https://github.com/${env.REPOSITORY}/releases/new?tag=${env.VERSION}&target=${env.MERGE_SHA}) (this link pre-populates the tag and target fields).
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

const payload = {
    body: bodyText()
};

execSync(`curl -X POST \
    ${pr_event.comments_url} \
    -H "authorization: Bearer $GITHUB_TOKEN" \
    -H "content-type: application/json" \
    --data '${stringify(payload)}' \
    ${curlOpts}`
);



function closeMilestone() {
    if (pr_event.milestone) {
        const payload = {
            state: 'closed'
        };
        try {
            execSync(`curl -X PATCH \
                https://api.github.com/repos/${env.REPOSITORY}/milestones/${pr_event.milestone.number} \
                -H "authorization: Bearer $GITHUB_TOKEN" \
                -H "content-type: application/json" \
                --data '${stringify(payload)}' \
                ${curlOpts}`
            );
            return true;
        } catch (err) {
            console.log(`::warning:: Error closing milestone ${pr_event.milestone.title}`);
            console.log(err, '\n');
        }
    }
    return false;
}

function updatePRTitle() {
    const payload = {
        title: `[${env.JOB_STATUS}] ${pr_event.title}`
    };
    execSync(`curl -X PATCH \
        ${pr_event.url} \
        -H "authorization: Bearer $GITHUB_TOKEN" \
        -H "content-type: application/json" \
        --data '${stringify(payload)}' \
        ${curlOpts}`
    );
}
