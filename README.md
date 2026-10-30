# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/JoeMountWSWS/explainer-studio/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                         |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|----------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| tools/studio/\_\_init\_\_.py |        0 |        0 |        0 |        0 |    100% |           |
| tools/studio/build.py        |      118 |        0 |       30 |        0 |    100% |           |
| tools/studio/cli.py          |      228 |       60 |       36 |        0 |     70% |104-105, 115-118, 122-146, 151-177, 221-231 |
| tools/studio/common.py       |      112 |        4 |       38 |        4 |     95% |17, 117, 165-166, 186-\>183, 202-\>exit |
| tools/studio/music.py        |       45 |        0 |        6 |        0 |    100% |           |
| tools/studio/render.py       |      199 |        3 |       60 |        0 |     99% |     62-64 |
| tools/studio/script.py       |      112 |        1 |       46 |        3 |     97% |129, 136-\>113, 149-\>146 |
| tools/studio/setup.py        |      113 |       13 |       34 |        4 |     87% |116-125, 136-137, 155-\>161, 158, 171 |
| tools/studio/skill.py        |       35 |        1 |       10 |        1 |     96% |        25 |
| tools/studio/voice.py        |      449 |      103 |      136 |        3 |     78% |119-134, 145-147, 174-193, 197, 202-204, 208-214, 217-218, 257-270, 274-285, 289-294, 314-322, 325-330, 401-404, 429-\>exit, 466-467, 530-532, 592-\>595, 626-\>629 |
| **TOTAL**                    | **1411** |  **185** |  **396** |   **15** | **87%** |           |


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