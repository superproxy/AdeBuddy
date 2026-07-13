import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import { api } from '../api/client'
import { runSse } from '../api/sse'
import { useUiStore } from './ui'
import { useSyncStore } from './sync'

export const MCP_SOURCE_ORDER = ['registry', 'smithery', 'modelscope', 'pulsemcp', 'glama'] as const
export type McpSourceId = (typeof MCP_SOURCE_ORDER)[number]

export const MCP_SOURCE_LABELS: Record<McpSourceId, string> = {
  registry: 'Official Registry',
  smithery: 'Smithery',
  modelscope: 'ModelScope',
  pulsemcp: 'PulseMCP',
  glama: 'Glama',
}

/** 默认启用源：不含 PulseMCP（需 API Key，旧接口已日落） */
export const MCP_SOURCE_DEFAULT: McpSourceId[] = ['registry', 'smithery', 'modelscope', 'glama']

export const PULSEMCP_DOCS_URL = 'https://www.pulsemcp.com/api/docs/v0.1'
export const PULSEMCP_API_URL = 'https://www.pulsemcp.com/api'
export const PULSEMCP_MAILTO = 'mailto:hello@pulsemcp.com'

export const useMcpStore = defineStore('mcp', () => {
  const ui = useUiStore()
  const sync = useSyncStore()
  const mcpTemplate = reactive<any>({ mcpServers: {} })
  const mcpConfigData = reactive<any>({ mcp: {} })
  const mcpTab = ref<'market' | 'manual'>('market')
  const mcpMarketQ = ref('')
  const mcpMarketResults = ref<any[]>([])
  const mcpSearched = ref(false)
  const mcpMarketLoading = ref(false)
  const mcpMarketMeta = ref<any>(null)
  const mcpMarketSources = ref<McpSourceId[]>([...MCP_SOURCE_DEFAULT])
  const pulseMcpConfigured = ref(false)
  const mcpForm = reactive({ name: '', type: '', command: '', args: '', url: '', headers: '', env: '', paste: '' })
  const editingMcp = ref('')
  const editMcpForm = reactive({ type: '', command: '', args: '', url: '', headers: '', env: '' })
  const listFilter = ref<'all' | 'on' | 'off'>('all')
  const listQuery = ref('')

  const mcpServerEntries = computed(() =>
    Object.entries(mcpTemplate.mcpServers || {}).map(([name, cfg]: [string, any]) => ({
      name,
      cfg,
      enabled: !(cfg?.disabled === true || cfg?.disabled === 'true'),
      cmd: cfg?.command ? `${cfg.command} ${(cfg.args || []).join(' ')}`.trim() : (cfg?.url || ''),
      type: cfg?.type || (cfg?.url ? 'http' : 'stdio'),
    })),
  )
  const mcpEnabledCount = computed(() => mcpServerEntries.value.filter((s) => s.enabled).length)
  const mcpDisabledCount = computed(() => mcpServerEntries.value.length - mcpEnabledCount.value)
  const mcpKeyCount = computed(() => Object.keys(mcpConfigData.mcp || {}).length)
  const filteredServers = computed(() => {
    const q = listQuery.value.trim().toLowerCase()
    return mcpServerEntries.value.filter((s) => {
      if (listFilter.value === 'on' && !s.enabled) return false
      if (listFilter.value === 'off' && s.enabled) return false
      if (!q) return true
      return s.name.toLowerCase().includes(q) || s.cmd.toLowerCase().includes(q) || s.type.toLowerCase().includes(q)
    })
  })

  async function loadMcpCatalog() {
    const r = await api<{ ok: boolean; data?: any }>('/api/mcp/list')
    if (r.ok) Object.assign(mcpTemplate, r.data)
  }
  async function loadMcpConfig() {
    const r = await api<{ ok: boolean; data?: any }>('/api/mcp-config')
    if (r.ok) {
      Object.keys(mcpConfigData.mcp).forEach((k) => delete mcpConfigData.mcp[k])
      Object.assign(mcpConfigData.mcp, (r.data && r.data.mcp) || {})
    }
    return r
  }
  async function loadPulseMcpStatus() {
    const r = await api<{ ok: boolean; configured?: boolean }>('/api/mcp/market-status')
    if (r.ok) pulseMcpConfigured.value = !!r.configured
    return r
  }

  async function toggleMarketSource(src: McpSourceId) {
    const cur = mcpMarketSources.value
    if (cur.includes(src)) {
      if (cur.length === 1) {
        ui.toast('至少保留一个数据源', 'warn')
        return
      }
      mcpMarketSources.value = cur.filter((s) => s !== src)
    } else {
      if (src === 'pulsemcp') {
        await loadPulseMcpStatus()
        const ok = await ui.askConfirm({
          title: '启用 PulseMCP？',
          message: pulseMcpConfigured.value
            ? '已检测到 PULSEMCP_API_KEY。将使用官方 v0.1 接口搜索。'
            : [
                'PulseMCP 正式 API（v0.1）需要申请 API Key。',
                '未配置 Key 时会回退旧接口，可能随机失败。',
                '',
                '配置方式：设置环境变量后重启应用',
                '  PULSEMCP_API_KEY=你的key',
                '  PULSEMCP_TENANT_ID=你的tenant（可选）',
              ].join('\n'),
          confirmText: pulseMcpConfigured.value ? '启用' : '仍要启用',
          cancelText: '取消',
          tone: 'brand',
          links: [
            { label: 'API 文档', href: PULSEMCP_DOCS_URL },
            { label: '申请 / 了解 API', href: PULSEMCP_API_URL },
            { label: '邮件申请 Key', href: PULSEMCP_MAILTO },
          ],
        })
        if (!ok) return
      }
      mcpMarketSources.value = MCP_SOURCE_ORDER.filter((s) => cur.includes(s) || s === src)
    }
    if (mcpSearched.value) searchMcpMarket()
  }

  async function searchMcpMarket() {
    if (!mcpMarketQ.value.trim()) {
      ui.toast('请输入搜索关键词', 'warn')
      return
    }
    if (!mcpMarketSources.value.length) {
      ui.toast('请至少选择一个数据源', 'warn')
      return
    }
    mcpSearched.value = true
    mcpMarketLoading.value = true
    try {
      const qs = new URLSearchParams({
        q: mcpMarketQ.value.trim(),
        sources: mcpMarketSources.value.join(','),
        limit: '12',
      })
      const r = await api<{ ok: boolean; data?: any[]; error?: string; meta?: any }>('/api/mcp/search?' + qs.toString())
      if (r.ok) {
        mcpMarketResults.value = r.data || []
        mcpMarketMeta.value = r.meta || null
      } else {
        mcpMarketResults.value = []
        mcpMarketMeta.value = null
        ui.toast('搜索失败: ' + r.error, 'err')
      }
    } finally {
      mcpMarketLoading.value = false
    }
  }

  function _mcpDetailQs(item: any) {
    const p = new URLSearchParams()
    if (item.source) p.set('source', item.source)
    if (item.id) p.set('id', String(item.id))
    if (item.owner) p.set('owner', item.owner)
    if (item.name) p.set('name', item.name)
    return p.toString()
  }
  async function getMcpDetail(item: any) {
    const r = await api<{ ok: boolean; data?: any; install?: any; install_error?: string; error?: string }>('/api/mcp/detail?' + _mcpDetailQs(item))
    if (!r.ok) { ui.toast('获取失败: ' + r.error, 'err'); return }
    const payload = {
      source: item.source || 'modelscope',
      install: r.install || null,
      install_error: r.install_error || null,
      detail: r.data,
    }
    ui.showModal((item.name || item.id || 'MCP') + ' · ' + (item.source_label || item.source || ''), JSON.stringify(payload, null, 2))
  }
  async function addMarketMcpToTemplate(item: any) {
    const localName = (item.name || item.id || 'mcp').toString().split('/').pop() || 'mcp'
    const r = await api<{ ok: boolean; data?: any; install?: any; install_error?: string; error?: string }>('/api/mcp/detail?' + _mcpDetailQs(item))
    if (!r.ok) { ui.toast('获取失败: ' + r.error, 'err'); return }
    let cfg: any = r.install?.server_config
    if (!cfg) {
      const data = r.data || {}
      const servers = data.servers || data.mcp_servers || []
      if (servers.length) {
        const s = servers[0]
        cfg = { type: s.type, url: s.url }
        if (data.auth_required) cfg.headers = { Authorization: 'Bearer ${MODELSCOPE_TOKEN}' }
      } else if (data.server_config) {
        cfg = data.server_config
      }
    }
    if (!cfg) {
      ui.toast(r.install_error || '该来源无法自动生成配置，请改用手动添加', 'warn')
      return
    }
    const key = r.install?.local_name || localName
    mcpTemplate.mcpServers[key] = cfg
    const sr = await api('/api/mcp/save', { method: 'POST', body: JSON.stringify({ data: mcpTemplate }) })
    sr.ok
      ? ui.toast('已添加 ' + key + (item.source_label || item.source ? `（${item.source_label || item.source}）` : ''))
      : ui.toast('保存失败: ' + sr.error, 'err')
  }
  async function toggleMcpDisabled(name: string, enabled: boolean) {
    mcpTemplate.mcpServers[name].disabled = !enabled
    await api('/api/mcp/save', { method: 'POST', body: JSON.stringify({ data: mcpTemplate }) })
  }
  async function deleteMcpEntry(name: string) {
    const ok = await ui.askConfirm({
      title: '删除此服务？',
      message: '将从已配置中移除，此操作不可撤销。',
      detail: name,
      confirmText: '确认删除',
      tone: 'danger',
    })
    if (!ok) return
    delete mcpTemplate.mcpServers[name]
    if (editingMcp.value === name) editingMcp.value = ''
    await api('/api/mcp/save', { method: 'POST', body: JSON.stringify({ data: mcpTemplate }) })
    ui.toast('已删除 ' + name)
  }
  async function saveMcpTemplate() {
    const r = await api<{ ok: boolean; error?: string }>('/api/mcp/save', { method: 'POST', body: JSON.stringify({ data: mcpTemplate }) })
    r.ok ? ui.toast('模板已保存') : ui.toast('保存失败: ' + r.error, 'err')
  }
  async function generateMcpRuntime() {
    const r = await api<{ ok: boolean; stdout?: string; stderr?: string; error?: string }>('/api/init-env', { method: 'POST' })
    if (r.ok) { ui.toast('mcp.json 已生成'); if (r.stdout) ui.showModal('init-env 输出', r.stdout + (r.stderr ? '\n--- stderr ---\n' + r.stderr : '')) }
    else ui.toast('生成失败: ' + r.error, 'err')
  }
  function parsePastedMcp() {
    if (!mcpForm.paste.trim()) { ui.toast('请粘贴配置', 'warn'); return }
    try {
      let p = JSON.parse(mcpForm.paste)
      if (p.mcpServers) p = p.mcpServers
      const k = Object.keys(p)[0]
      if (k) {
        const cfg = p[k]
        mcpForm.name = k
        if (cfg.command) mcpForm.command = cfg.command
        if (cfg.args) mcpForm.args = cfg.args.join(',')
        if (cfg.url) mcpForm.url = cfg.url
        if (cfg.type) mcpForm.type = cfg.type
        if (cfg.headers) mcpForm.headers = JSON.stringify(cfg.headers, null, 2)
        if (cfg.env) mcpForm.env = JSON.stringify(cfg.env, null, 2)
        ui.toast('已解析')
      }
    } catch (e: any) { ui.toast('JSON 解析失败: ' + e.message, 'err') }
  }
  async function addManualMcp() {
    if (!mcpForm.name.trim()) { ui.toast('name 必填', 'warn'); return }
    const cfg: any = {}
    if (mcpForm.type) cfg.type = mcpForm.type
    if (mcpForm.command) cfg.command = mcpForm.command
    if (mcpForm.args.trim()) cfg.args = mcpForm.args.split(',').map((s: string) => s.trim()).filter(Boolean)
    if (mcpForm.url) cfg.url = mcpForm.url
    try { if (mcpForm.headers.trim()) cfg.headers = JSON.parse(mcpForm.headers) } catch { ui.toast('headers JSON 错误', 'err'); return }
    try { if (mcpForm.env.trim()) cfg.env = JSON.parse(mcpForm.env) } catch { ui.toast('env JSON 错误', 'err'); return }
    mcpTemplate.mcpServers[mcpForm.name.trim()] = cfg
    const r = await api('/api/mcp/save', { method: 'POST', body: JSON.stringify({ data: mcpTemplate }) })
    if (r.ok) {
      ui.toast('已添加 ' + mcpForm.name)
      Object.assign(mcpForm, { name: '', type: '', command: '', args: '', url: '', headers: '', env: '', paste: '' })
    } else ui.toast('保存失败: ' + r.error, 'err')
  }
  async function toggleAllMcp(enabled: boolean) {
    for (const name of Object.keys(mcpTemplate.mcpServers || {})) {
      mcpTemplate.mcpServers[name].disabled = !enabled
    }
    await api('/api/mcp/save', { method: 'POST', body: JSON.stringify({ data: mcpTemplate }) })
    ui.toast(enabled ? '已全部启用' : '已全部禁用')
  }
  async function saveMcpAll(silent = false) {
    const r1 = await api('/api/mcp/save', { method: 'POST', body: JSON.stringify({ data: mcpTemplate }) })
    const r2 = await api('/api/mcp-config', { method: 'POST', body: JSON.stringify({ data: mcpConfigData }) })
    if (!silent) (r1.ok && r2.ok) ? ui.toast('mcp.yaml 已保存') : ui.toast('保存失败', 'err')
    return r1.ok && r2.ok
  }
  async function syncMcpFull() {
    if (sync.syncing) { ui.toast('正在同步中，请稍候', 'warn'); return }
    const r1 = await api('/api/mcp/save', { method: 'POST', body: JSON.stringify({ data: mcpTemplate }) })
    const r2 = await api('/api/mcp-config', { method: 'POST', body: JSON.stringify({ data: mcpConfigData }) })
    if (!r1.ok || !r2.ok) { ui.toast('保存 mcp.yaml 失败', 'err'); return }
    const g = await api('/api/init-env', { method: 'POST' })
    if (!g.ok) { ui.toast('生成 mcp.json 失败', 'err'); return }
    ui.clearLog()
    for (const ideKey of sync.syncTargetIdes) {
      await runSse('/api/init-ide?ide=' + encodeURIComponent(ideKey) + '&scope=mcp', (line) => ui.appendLog(line))
    }
  }
  function startEditMcp(name: string) {
    const cfg = mcpTemplate.mcpServers[name]
    editingMcp.value = name
    editMcpForm.type = cfg.type || ''
    editMcpForm.command = cfg.command || ''
    editMcpForm.args = (cfg.args || []).join(', ')
    editMcpForm.url = cfg.url || ''
    editMcpForm.headers = cfg.headers ? JSON.stringify(cfg.headers, null, 2) : ''
    editMcpForm.env = cfg.env ? JSON.stringify(cfg.env, null, 2) : ''
  }
  function cancelEditMcp() { editingMcp.value = '' }
  async function saveEditMcp() {
    const name = editingMcp.value
    if (!name) return
    const cfg = mcpTemplate.mcpServers[name]
    const disabled = cfg.disabled
    const newCfg: any = {}
    if (editMcpForm.type) newCfg.type = editMcpForm.type
    if (editMcpForm.command) newCfg.command = editMcpForm.command
    if (editMcpForm.args.trim()) newCfg.args = editMcpForm.args.split(',').map((s: string) => s.trim()).filter(Boolean)
    if (editMcpForm.url) newCfg.url = editMcpForm.url
    try { if (editMcpForm.headers.trim()) newCfg.headers = JSON.parse(editMcpForm.headers) } catch { ui.toast('headers JSON 错误', 'err'); return }
    try { if (editMcpForm.env.trim()) newCfg.env = JSON.parse(editMcpForm.env) } catch { ui.toast('env JSON 错误', 'err'); return }
    if (disabled !== undefined) newCfg.disabled = disabled
    mcpTemplate.mcpServers[name] = newCfg
    editingMcp.value = ''
    const r = await api('/api/mcp/save', { method: 'POST', body: JSON.stringify({ data: mcpTemplate }) })
    r.ok ? ui.toast('已保存 ' + name) : ui.toast('保存失败: ' + r.error, 'err')
  }
  async function saveMcpConfig() {
    const r = await api('/api/mcp-config', { method: 'POST', body: JSON.stringify({ data: mcpConfigData }) })
    r.ok ? ui.toast('mcp.yaml 已保存') : ui.toast('保存失败: ' + r.error, 'err')
  }
  async function addMcpConfigKey() {
    const key = await ui.askPrompt({
      title: '添加密钥',
      message: '写入 mcp.yaml，生成 mcp.json 时替换 ${KEY}。',
      label: '密钥名称',
      placeholder: '例如 TAVILY_API_KEY / MODELSCOPE_TOKEN',
      confirmText: '添加',
      mono: true,
      validate: (v) => {
        if (!v) return '请输入密钥名称'
        if (mcpConfigData.mcp[v]) return 'Key 已存在'
        if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(v)) return '仅支持字母、数字、下划线，且不能以数字开头'
        return null
      },
    })
    if (!key) return
    mcpConfigData.mcp[key.trim()] = ''
    ui.toast('已添加: ' + key.trim())
  }
  async function deleteMcpConfigKey(key: string) {
    const ok = await ui.askConfirm({
      title: '删除密钥？',
      message: '删除后不可恢复。',
      detail: key,
      confirmText: '确认删除',
      tone: 'danger',
    })
    if (!ok) return
    const r = await api('/api/mcp-config/key/' + encodeURIComponent(key), { method: 'DELETE' })
    if (r.ok) { delete mcpConfigData.mcp[key]; ui.toast('已删除') }
    else ui.toast('删除失败: ' + r.error, 'err')
  }

  return {
    mcpTemplate, mcpConfigData, mcpTab, mcpMarketQ, mcpMarketResults, mcpSearched,
    mcpMarketLoading, mcpMarketMeta, mcpMarketSources, pulseMcpConfigured,
    mcpForm, editingMcp, editMcpForm,
    listFilter, listQuery,
    mcpServerEntries, filteredServers, mcpEnabledCount, mcpDisabledCount, mcpKeyCount,
    MCP_SOURCE_ORDER, MCP_SOURCE_LABELS,
    loadMcpCatalog, loadMcpConfig, loadPulseMcpStatus, searchMcpMarket, toggleMarketSource,
    getMcpDetail, addMarketMcpToTemplate,
    toggleMcpDisabled, deleteMcpEntry, saveMcpTemplate, generateMcpRuntime,
    parsePastedMcp, addManualMcp, toggleAllMcp, saveMcpAll, syncMcpFull,
    startEditMcp, cancelEditMcp, saveEditMcp, saveMcpConfig, addMcpConfigKey, deleteMcpConfigKey,
  }
})
