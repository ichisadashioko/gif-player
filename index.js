const { app, BrowserWindow } = require('electron')

let mainWindow = null

function createWindow() {
  const windowOptions = {
    width: 1080,
    minWidth: 680,
    height: 840,
    title: app.name,
    webPreferences: {
      nodeIntegration: true,
    },
  }

  mainWindow = new BrowserWindow(windowOptions)

  mainWindow.loadFile('index.html')

  mainWindow.on('closed', function () {
    mainWindow = null
  })
}

app.on('ready', createWindow)