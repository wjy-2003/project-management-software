## 说明
* https://learn.microsoft.com/zh-cn/visualstudio/liveshare/use/share-project-join-session-visual-studio-code

Code-server 本身不直接集成Live Share，但可以通过安装适用于VS Code (Code - OSS) 的Live Share 扩展来在Code-server 环境中实现Live Share 功能。 安装后，用户可以像在本地VS Code 中一样，通过点击Live Share 按钮生成或粘贴邀请链接来启动或加入协作会话，实现远程结对编程、代码评审或在线教学等协作功能。 

在Code-server 中启用Live Share 的步骤：

  1. 安装Live Share 扩展：
  
  打开Code-server，在扩展视图中搜索并安装 Live Share 扩展。 
  安装完成后，根据提示重新加载Code-server。 
  
  2. 登录Live Share：
  
  在Code-server 左下角状态栏找到Live Share 图标。 
  点击图标，选择登录（支持GitHub 或Microsoft 账户），以身份验证你的身份。 

  3. 发起或加入协作会话：

  发起会话：: 点击Live Share 图标，选择“共享项目”或“Share”选项。 VS Code 会生成一个邀请链接。 
  加入会话：: 点击Live Share 图标，选择“加入协作会话”，然后粘贴你收到的邀请URL 并确认。 

 4. Live Share 提供的协作功能： 

  结对编程： 实时同步代码，实现远程协作开发，掘金 在线开发就像面对面一样自然。
  代码评审与辅导： 导师可以实时查看代码，指出问题，并示范修改，掘金 提高效率。
  在线教学与演示： 主讲人可以实时展示代码变动，让参与者直接看到并互动。
  调试协作： 团队成员可以一起查找bug，共享调试器状态和调用栈。
  
## 共同编辑方法
在VSCode中进行共同编辑有多种方式，可以选择适合自己的方式来进行协作编辑。下面介绍一些常用的方法： 
1. 使用Live Share扩展：VSCode提供了一个名为Live Share的扩展，可以让多个用户共同编辑同一个文件。可以通过以下步骤使用：    – 安装Live Share扩展：打开VSCode，点击左侧的扩展图标，搜索“Live Share”，点击安装。
   – 启动Live Share：在VSCode中打开要共同编辑的文件，点击右下角的Live Share图标，选择“Start Collaboration”。
   – 邀请其他人：生成一个共享链接，并将链接发送给其他人，其他人可以通过链接加入共同编辑。
   – 共同编辑：多个用户可以同时在同一个文件中进行编辑，修改会实时同步。
2. 使用Git进行协作：如果多个人共同编辑的项目使用了版本控制工具如Git，可以通过以下步骤进行协作编辑：    – 在Git仓库中创建一个分支：每个参与协作的用户在本地创建一个分支，以便单独进行编辑。
   – 修改文件：每个用户在自己的分支上进行编辑，修改完成后提交修改。
   – 合并修改：一个用户将自己的修改合并到主分支上，其他用户可以通过更新主分支来获取最新的修改。 3. 使用协作工具：除了VSCode的Live Share和Git，还可以使用其他协作工具来进行共同编辑，如Google Docs、Microsoft Office等。用户可以选择适合自己的工具来进行协作编辑。

## VS live share 用法：
* cplusplus.com/reference/cstring/memset/?kw=memset 
* https://docs.github.com/zh/codespaces/developing-in-a-codespace/working-collaboratively-in-a-codespace#sharing-your-codespace-with-someone-else
