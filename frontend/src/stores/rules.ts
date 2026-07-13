import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api/client'
import { useUiStore } from './ui'

export interface RuleItem {
  name: string
  path: string
  category: string
  description: string
  alwaysApply: boolean
  globs: string
  scene: string
  source: 'config' | 'template'
  size: number
}

export const useRulesStore = defineStore('rules', () => {
  const ui = useUiStore()
  const rules = ref<RuleItem[]>([])
  const selectedRulePath = ref('')
  const editingContent = ref('')
  const editingMeta = ref({ description: '', alwaysApply: false, globs: '', scene: '' })
  const dirty = ref(false)

  const ruleCategories = computed(() => [...new Set(rules.value.map((r) => r.category).filter(Boolean))].sort())
  const selectedRule = computed(() => rules.value.find((r) => r.path === selectedRulePath.value))
  const groupedRules = computed(() => {
    const groups: Record<string, RuleItem[]> = {}
    for (const r of rules.value) {
      const cat = r.category || '根目录'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(r)
    }
    return groups
  })

  async function loadRules() {
    const r = await api<{ ok: boolean; data?: RuleItem[]; count?: number }>('/api/rules')
    if (r.ok) rules.value = r.data || []
  }

  async function selectRule(path: string) {
    selectedRulePath.value = path
    const r = await api<{ ok: boolean; content?: string; writable?: boolean; error?: string }>(
      '/api/rules/content?path=' + encodeURIComponent(path),
    )
    if (r.ok) {
      editingContent.value = r.content || ''
      // 解析 frontmatter
      const rule = rules.value.find((x) => x.path === path)
      if (rule) {
        editingMeta.value = {
          description: rule.description,
          alwaysApply: rule.alwaysApply,
          globs: rule.globs,
          scene: rule.scene,
        }
      }
      dirty.value = false
    } else {
      ui.toast('加载失败: ' + (r.error || ''), 'err')
    }
  }

  function onContentChange() {
    dirty.value = true
  }

  async function saveRule() {
    if (!selectedRulePath.value) return
    // 重新组装 frontmatter + body
    const body = editingContent.value
    // 提取 body（去掉旧 frontmatter）
    let bodyOnly = body
    if (body.startsWith('---')) {
      const parts = body.split('---', 3)
      bodyOnly = parts.length >= 3 ? parts[2].trim() : body
    }
    const fm: string[] = ['---']
    if (editingMeta.value.description)
      fm.push(`description: ${editingMeta.value.description}`)
    if (editingMeta.value.alwaysApply)
      fm.push(`alwaysApply: true`)
    else
      fm.push(`alwaysApply: false`)
    if (editingMeta.value.globs)
      fm.push(`globs: ${editingMeta.value.globs}`)
    if (editingMeta.value.scene)
      fm.push(`scene: ${editingMeta.value.scene}`)
    fm.push('---', '')
    const content = fm.join('\n') + '\n' + bodyOnly + '\n'

    const r = await api<{ ok: boolean; error?: string }>('/api/rules/save', {
      method: 'POST',
      body: JSON.stringify({ path: selectedRulePath.value, content }),
    })
    if (r.ok) {
      ui.toast('规则已保存')
      dirty.value = false
      await loadRules()
    } else {
      ui.toast('保存失败: ' + (r.error || ''), 'err')
    }
  }

  async function deleteRule(path: string) {
    const rule = rules.value.find((r) => r.path === path)
    if (rule?.source === 'template') {
      ui.toast('预置规则不可删除', 'warn')
      return
    }
    if (!confirm('删除规则 ' + path + '?')) return
    const r = await api<{ ok: boolean; error?: string }>(
      '/api/rules?path=' + encodeURIComponent(path),
      { method: 'DELETE' },
    )
    if (r.ok) {
      ui.toast('已删除')
      if (selectedRulePath.value === path) {
        selectedRulePath.value = ''
        editingContent.value = ''
      }
      await loadRules()
    } else {
      ui.toast('删除失败: ' + (r.error || ''), 'err')
    }
  }

  function newRule() {
    const name = prompt('输入规则文件名（不含 .md 扩展名）:', 'new-rule')
    if (!name) return
    const safeName = name.replace(/[^a-zA-Z0-9\-_]/g, '-')
    const path = safeName + '.md'
    editingMeta.value = { description: '', alwaysApply: false, globs: '', scene: '' }
    editingContent.value = '# ' + safeName + '\n\n在此编写规则内容...\n'
    selectedRulePath.value = path
    dirty.value = true
    rules.value = [
      {
        name: safeName,
        path,
        category: '',
        description: '',
        alwaysApply: false,
        globs: '',
        scene: '',
        source: 'config',
        size: 0,
      },
      ...rules.value,
    ]
  }

  async function syncRules() {
    const r = await api<{ ok: boolean; count?: number; message?: string; error?: string }>(
      '/api/rules/sync',
      { method: 'POST' },
    )
    if (r.ok) ui.toast(r.message || `已同步 ${r.count} 个规则`)
    else ui.toast('同步失败: ' + (r.error || ''), 'err')
  }

  function exportRules() {
    window.location.href = '/api/rules/export'
  }

  async function importRules(e: Event) {
    const input = e.target as HTMLInputElement
    const f = input.files && input.files[0]
    if (!f) return
    const fd = new FormData()
    fd.append('file', f)
    fd.append('overwrite', 'true')
    const resp = await fetch('/api/rules/import', { method: 'POST', body: fd })
    const res = await resp.json() as { ok: boolean; count?: number; error?: string }
    input.value = ''
    if (res.ok) {
      ui.toast(`导入成功: ${res.count} 个规则`)
      await loadRules()
    } else {
      ui.toast('导入失败: ' + (res.error || ''), 'err')
    }
  }

  return {
    rules,
    selectedRulePath,
    editingContent,
    editingMeta,
    dirty,
    ruleCategories,
    selectedRule,
    groupedRules,
    loadRules,
    selectRule,
    onContentChange,
    saveRule,
    deleteRule,
    newRule,
    syncRules,
    exportRules,
    importRules,
  }
})
