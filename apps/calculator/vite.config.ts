import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const repository = process.env.GITHUB_REPOSITORY?.split('/').pop()
const base = process.env.BASE_PATH ?? (repository ? `/${repository}/` : '/')

export default defineConfig({
  plugins: [react()],
  base,
})
