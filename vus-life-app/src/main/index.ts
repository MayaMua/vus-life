import { app, shell, BrowserWindow, ipcMain, dialog } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import type Store from 'electron-store'
import icon from '../../resources/icon.png?asset'

const DEFAULT_WIDTH = 1280
const DEFAULT_HEIGHT = 800

type WindowBounds = { x: number; y: number; width: number; height: number }

function createWindow(windowStore: Store<{ bounds?: WindowBounds }>): void {
  const savedBounds = windowStore.get('bounds')
  const width = savedBounds?.width ?? DEFAULT_WIDTH
  const height = savedBounds?.height ?? DEFAULT_HEIGHT
  const x = savedBounds?.x
  const y = savedBounds?.y

  const mainWindow = new BrowserWindow({
    width,
    height,
    ...(typeof x === 'number' && typeof y === 'number' ? { x, y } : {}),
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  const saveBounds = (): void => {
    const b = mainWindow.getBounds()
    windowStore.set('bounds', { x: b.x, y: b.y, width: b.width, height: b.height })
  }

  mainWindow.on('resize', saveBounds)
  mainWindow.on('move', saveBounds)
  mainWindow.on('close', saveBounds)

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(async () => {
  // Dynamic import so ESM-only electron-store works when main is compiled to CJS
  const { default: Store } = await import('electron-store')
  const windowStore = new Store<{ bounds?: WindowBounds }>({ name: 'window-state' })

  // Set app user model id for windows
  electronApp.setAppUserModelId('com.electron')

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // IPC test
  ipcMain.on('ping', () => console.log('pong'))

  // Folder selection for General Settings storage path
  ipcMain.handle('open-folder-dialog', async (event) => {
    const win = BrowserWindow.fromWebContents(event.sender) ?? BrowserWindow.getFocusedWindow()
    if (!win) return null
    const result = await dialog.showOpenDialog(win, { properties: ['openDirectory'] })
    return result.canceled ? null : result.filePaths[0] ?? null
  })

  createWindow(windowStore)

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow(windowStore)
  })
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.
