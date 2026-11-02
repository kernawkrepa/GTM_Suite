const { app, BrowserWindow, ipcMain, shell, dialog, session } = require('electron')
const path = require('path')
const net = require('net')
const { spawn } = require('child_process')

let mainWindow = null
let backendProcess = null
let backendPort = null

async function findFreePort(start = 8741) {
  return new Promise((resolve) => {
    const server = net.createServer()
    server.listen(start, '127.0.0.1', () => {
      const port = server.address().port
      server.close(() => resolve(port))
    })
    server.on('error', () => resolve(findFreePort(start + 1)))
  })
}

async function startBackend(port) {
  const isProd = app.isPackaged
  const dataDir = path.join(app.getPath('userData'), 'data')

  let pythonExe, cwd
  if (isProd) {
    pythonExe = path.join(process.resourcesPath, 'backend', 'python', 'python')
    cwd = process.resourcesPath
  } else {
    pythonExe = process.platform === 'win32' ? 'python' : 'python3'
    cwd = path.join(__dirname, '..')
  }

  const env = {
    ...process.env,
    GTM_DATA_DIR: dataDir,
    GTM_PORT: String(port),
  }

  backendProcess = spawn(
    pythonExe,
    ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', String(port)],
    { cwd, env, stdio: ['ignore', 'pipe', 'pipe'] }
  )

  backendProcess.stdout.on('data', (d) => console.log('[backend]', d.toString().trim()))
  backendProcess.stderr.on('data', (d) => console.error('[backend]', d.toString().trim()))
  backendProcess.on('exit', (code) => console.log('[backend] exited with code', code))
}

async function waitForBackend(port, retries = 30) {
  for (let i = 0; i < retries; i++) {
    try {
      const resp = await fetch(`http://127.0.0.1:${port}/health`)
      if (resp.ok) return
    } catch (_) {}
    await new Promise((r) => setTimeout(r, 500))
  }
  throw new Error('Backend did not start in time')
}

function patchTwitchHeaders() {
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    const url = details.url || ''
    const isTwitch = url.includes('clips.twitch.tv') || url.includes('player.twitch.tv')
    if (!isTwitch) {
      callback({ responseHeaders: details.responseHeaders })
      return
    }
    const headers = { ...details.responseHeaders }
    delete headers['x-frame-options']
    delete headers['X-Frame-Options']
    delete headers['content-security-policy']
    delete headers['Content-Security-Policy']
    callback({ responseHeaders: headers })
  })
}

function createWindow(port) {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    frame: false,
    backgroundColor: '#0e0e10',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL)
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.send('backend-port', port)
  })

  mainWindow.on('closed', () => { mainWindow = null })
}

app.whenReady().then(async () => {
  patchTwitchHeaders()
  backendPort = await findFreePort(8741)
  await startBackend(backendPort)
  await waitForBackend(backendPort)
  createWindow(backendPort)
})

app.on('window-all-closed', () => {
  if (backendProcess) { backendProcess.kill(); backendProcess = null }
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (!mainWindow) createWindow(backendPort)
})

ipcMain.handle('get-backend-port', () => backendPort)
ipcMain.handle('open-folder', (_, p) => shell.openPath(p))
ipcMain.handle('open-external', (_, url) => shell.openExternal(url))
ipcMain.handle('show-save-dialog', async (_, opts) => dialog.showSaveDialog(mainWindow, opts))
ipcMain.handle('show-open-dialog', async (_, opts) => dialog.showOpenDialog(mainWindow, opts))
ipcMain.on('window-minimize', () => mainWindow?.minimize())
ipcMain.on('window-maximize', () => {
  if (mainWindow?.isMaximized()) mainWindow.unmaximize()
  else mainWindow?.maximize()
})
ipcMain.on('window-close', () => mainWindow?.close())
