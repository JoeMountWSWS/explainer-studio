# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/JoeMountWSWS/explainer-studio/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                         |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|----------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| tools/studio/\_\_init\_\_.py |        0 |        0 |        0 |        0 |    100% |           |
| tools/studio/build.py        |      118 |        0 |       30 |        0 |    100% |           |
| tools/studio/cli.py          |      257 |       54 |       48 |        0 |     77% |118-119, 168-190, 195-221, 267-277 |
| tools/studio/common.py       |      112 |        4 |       38 |        4 |     95% |17, 118, 166-167, 187-\>184, 203-\>exit |
| tools/studio/music.py        |       45 |        0 |        6 |        0 |    100% |           |
| tools/studio/render.py       |      204 |        0 |       62 |        0 |    100% |           |
| tools/studio/script.py       |      112 |        1 |       46 |        3 |     97% |129, 136-\>113, 149-\>146 |
| tools/studio/setup.py        |      113 |       13 |       34 |        4 |     87% |117-126, 137-138, 156-\>162, 159, 172 |
| tools/studio/skill.py        |       35 |        1 |       10 |        1 |     96% |        25 |
| tools/studio/verify.py       |      174 |       16 |       50 |        7 |     88% |41, 53, 92-93, 152, 163, 208, 222-230 |
| tools/studio/voice.py        |      453 |      102 |      136 |        3 |     78% |119-134, 145-147, 174-193, 197, 202-204, 208-214, 217-218, 257-271, 275-287, 291-296, 316-324, 327-332, 403-406, 431-\>exit, 538-540, 600-\>603, 634-\>637 |
| **TOTAL**                    | **1623** |  **191** |  **460** |   **22** | **88%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/JoeMountWSWS/explainer-studio/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/JoeMountWSWS/explainer-studio/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/JoeMountWSWS/explainer-studio/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/JoeMountWSWS/explainer-studio/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FJoeMountWSWS%2Fexplainer-studio%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/JoeMountWSWS/explainer-studio/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.