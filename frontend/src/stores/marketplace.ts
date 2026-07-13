import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'
import { useUiStore } from './ui'
import { useSkillStore } from './skill'
import { usePluginStore } from './plugin'

export interface MarketItem {
  id: string
  name: string
  version: string
  description: string
  author: string
  file: string
  size: number
  published_at: string
  tags: string[]
  downloads: number
}

export const useMarketplaceStore = defineStore('marketplace', () => {
  const ui = useUiStore()
  const skill = useSkillStore()
  const plugin = usePluginStore()

  const items = ref<MarketItem[]>([])
  const loading = ref(false)
  const searchQuery = ref('')
  const installing = ref('')  // 正在安装的 item id

  /** 浏览市场（支持搜索） */
  async function browse(q?: string) {
    loading.value = true
    try {
      const query = q !== undefined ? q : searchQuery.value
      const params = query.trim() ? '?q=' + encodeURIComponent(query.trim()) : ''
      const r = await api<{ ok: boolean; data?: MarketItem[]; total?: number }>('/api/marketplace' + params)
      if (r.ok) items.value = r.data || []
    } finally {
      loading.value = false
    }
  }

  /** 发布插件到市场 */
  async function publish(file: string, tags: string[] = []) {
    const r = await api<{ ok: boolean; data?: MarketItem; error?: string }>(
      '/api/marketplace/publish',
      { method: 'POST', body: JSON.stringify({ file, tags }) }
    )
    if (r.ok) {
      ui.toast(`已发布「${r.data?.name || file}」到市场`)
      browse()  // 刷新列表
    } else {
      ui.toast('发布失败: ' + (r.error || ''), 'err')
    }
    return r.ok
  }

  /** 从市场安装插件 */
  async function install(id: string) {
    if (installing.value) { ui.toast('正在安装其他插件，请稍候', 'warn'); return false }
    installing.value = id
    try {
      const r = await api<{
        ok: boolean; error?: string;
        plugin_count?: number; skill_count?: number; extras_count?: number;
        skipped?: any[]
      }>('/api/marketplace/install?id=' + encodeURIComponent(id))
      if (r.ok) {
        const parts: string[] = []
        if (r.plugin_count) parts.push(`${r.plugin_count} 个插件`)
        if (r.skill_count) parts.push(`${r.skill_count} 个技能`)
        if (r.extras_count) parts.push(`${r.extras_count} 项扩展`)
        const detail = parts.length ? '：' + parts.join('、') : ''
        const skippedNote = r.skipped?.length ? `，跳过 ${r.skipped.length} 项` : ''
        ui.toast('安装成功' + detail + skippedNote)
        // 刷新相关列表
        plugin.refreshPluginList()
        skill.loadInstalledSkills()
        // 增加本地下载计数
        const item = items.value.find(i => i.id === id)
        if (item) item.downloads = (item.downloads || 0) + 1
        return true
      } else {
        ui.toast('安装失败: ' + (r.error || ''), 'err')
        return false
      }
    } finally {
      installing.value = ''
    }
  }

  /** 从市场移除 */
  async function remove(id: string) {
    if (!confirm('确认从市场移除该插件？')) return false
    const r = await api<{ ok: boolean; error?: string }>(
      '/api/marketplace/remove?id=' + encodeURIComponent(id),
      { method: 'DELETE' }
    )
    if (r.ok) {
      ui.toast('已从市场移除')
      items.value = items.value.filter(i => i.id !== id)
      return true
    } else {
      ui.toast('移除失败: ' + (r.error || ''), 'err')
      return false
    }
  }

  return {
    items, loading, searchQuery, installing,
    browse, publish, install, remove,
  }
})
