const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 8080,
    client: {
      // 忽略 ResizeObserver 错误
      overlay: {
        runtimeErrors: (error) => {
          if (error.message && error.message.includes('ResizeObserver loop')) {
            return false
          }
          return true
        }
      }
    },
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      },
      '/socket.io': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        ws: true,
        secure: false
      }
    }
  },
  outputDir: '../dist',
  assetsDir: 'static'
})
