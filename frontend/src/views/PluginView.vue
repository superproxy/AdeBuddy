<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { usePluginStore } from '../stores/plugin'
import { useUiStore } from '../stores/ui'

const emit = defineEmits<{ 'go-tab': [key: string] }>()

const plugin = usePluginStore()
const ui = useUiStore()
const { plugins, installingPlugin, selectedForExport } = storeToRefs(plugin)
const {
  refreshPluginList, exportPlugin, onImportPluginFile, importPluginFile,
  onTogglePlugin, editPlugin, toggleSelectForExport, selectFilesForExport,
  clearExportSelection, exportSelectedPlugins, publishToMarketplace,
} = plugin

const inputRef = ref<HTMLInputElement | null>(null)
const listQuery = ref('')
const listFilter = ref<'all' | 'on' | 'off'>('all')
const exportMenu = ref<string | null>(null)
const dragging = ref(false)
const dragCounter = ref(0)

const installedCount = computed(() => plugins.value.filter((p) => p.installed).length)
const uninstalledCount = computed(() => plugins.value.length - installedCount.value)
const skillsTotal = computed(() => plugins.value.reduce((a, p) => a + (p.skills_count || 0), 0))

const filteredPlugins = computed(() => {
  const q = listQuery.value.trim().toLowerCase()
  return plugins.value.filter((p) => {
    if (listFilter.value === 'on' && !p.installed) return false
    if (listFilter.value === 'off' && p.installed) return false
    if (!q) return true
    return p.name.toLowerCase().includes(q) || (p.description || '').toLowerCase().includes(q)
  })
})

function triggerImport() { inputRef.value?.click() }

function onExportBatch() {
  if (!selectedForExport.value.size) {
    ui.toast('请先勾选要导出的插件', 'warn')
    return
  }
  exportSelectedPlugins()
}

function selectVisible() {
  selectFilesForExport(filteredPlugins.value.map((p) => p.file))
}

function goBuild() {
  emit('go-tab', 'plugin-build')
}

function onEdit(file: string) {
  editPlugin(file)
  emit('go-tab', 'plugin-build')
}

function toggleExportMenu(file: string) {
  exportMenu.value = exportMenu.value === file ? null : file
}

function doExport(file: string, format: 'zip' | 'yaml') {
  exportPlugin(file, format)
  exportMenu.value = null
}

function onDocClick(e: MouseEvent) {
  const t = e.target as HTMLElement
  if (!t.closest('.export-menu')) exportMenu.value = null
}

function onDragEnter(e: DragEvent) {
  if (!e.dataTransfer?.types?.includes('Files')) return
  e.preventDefault()
  dragCounter.value++
  dragging.value = true
}
function onDragOver(e: DragEvent) {
  if (!e.dataTransfer?.types?.includes('Files')) return
  e.preventDefault()
}
function onDragLeave(e: DragEvent) {
  e.preventDefault()
  dragCounter.value = Math.max(0, dragCounter.value - 1)
  if (dragCounter.value === 0) dragging.value = false
}
async function onDrop(e: DragEvent) {
  e.preventDefault()
  dragCounter.value = 0
  dragging.value = false
  const f = e.dataTransfer?.files?.[0]
  if (!f) return
  const ok = /\.(ya?ml|zip)$/i.test(f.name)
  if (!ok) {
    ui.toast('仅支持 .zip / .yaml / .yml', 'warn')
    return
  }
  await importPluginFile(f)
}

onMounted(() => {
  refreshPluginList()
  document.addEventListener('click', onDocClick)
})
onUnmounted(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <div
    class="plugin-page"
    @dragenter="onDragEnter"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
  >
    <div class="plugin-head flex flex-wrap items-start justify-between gap-4">
      <div class="min-w-0">
        <h1 class="text-[15px] font-semibold text-ink-900 m-0">插件配置</h1>
        <p class="text-xs text-ink-500 mt-1 mb-0">集中管理本地智能体插件 · 安装、导入导出与分享到市场</p>
      </div>
      <div class="btn-cluster">
        <button type="button" class="btn btn-secondary" @click="refreshPluginList">刷新</button>
        <button type="button" class="btn btn-secondary" @click="triggerImport">导入</button>
        <button
          type="button"
          class="btn btn-secondary"
          :disabled="!plugins.length"
          @click="onExportBatch"
        >导出</button>
        <button type="button" class="btn btn-primary" @click="goBuild">构建插件</button>
        <input ref="inputRef" type="file" accept=".yaml,.yml,.zip" class="hidden" @change="onImportPluginFile">
      </div>
    </div>

    <div class="kpis">
      <div class="kpi brand"><b>{{ plugins.length }}</b><span>插件总数</span><em>本地可用</em></div>
      <div class="kpi live"><b>{{ installedCount }}</b><span>已安装</span><em>已写入配置</em></div>
      <div class="kpi"><b>{{ skillsTotal }}</b><span>Skills 合计</span><em>所有插件汇总</em></div>
      <div class="kpi warn"><b>{{ uninstalledCount }}</b><span>未安装</span><em>可一键安装</em></div>
    </div>

    <section class="panel">
      <div class="toolbar">
        <div class="toolbar-left">
          <label class="search">
            <input v-model="listQuery" type="search" placeholder="筛选名称 / 描述" />
          </label>
          <div class="seg" role="group" aria-label="安装状态">
            <button type="button" :class="{ on: listFilter === 'all' }" @click="listFilter = 'all'">全部</button>
            <button type="button" :class="{ on: listFilter === 'on' }" @click="listFilter = 'on'">已安装</button>
            <button type="button" :class="{ on: listFilter === 'off' }" @click="listFilter = 'off'">未安装</button>
          </div>
        </div>
        <div class="btn-cluster">
          <div class="btn-pair" role="group" aria-label="批量选择">
            <button type="button" class="btn btn-ghost btn-sm" @click="selectVisible">全选可见</button>
            <button type="button" class="btn btn-ghost btn-sm" @click="clearExportSelection">清空</button>
          </div>
        </div>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th style="width:48px">选择</th>
              <th>插件</th>
              <th>描述</th>
              <th style="width:80px">Skills</th>
              <th style="width:80px">MCP</th>
              <th style="width:90px">状态</th>
              <th style="width:220px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in filteredPlugins" :key="p.file" :class="{ disabled: !p.installed }">
              <td>
                <input
                  type="checkbox"
                  class="pick"
                  :checked="selectedForExport.has(p.file)"
                  :aria-label="'选择 ' + p.name"
                  @change="toggleSelectForExport(p.file)"
                >
              </td>
              <td>
                <div class="name">{{ p.name }}<span class="ver">v{{ p.version }}</span></div>
              </td>
              <td><div class="desc" :title="p.description">{{ p.description || '—' }}</div></td>
              <td><span class="num-cell">{{ p.skills_count || 0 }}</span></td>
              <td><span class="num-cell">{{ p.mcp_count || 0 }}</span></td>
              <td>
                <span class="status" :class="p.installed ? 'on' : 'off'"><i />{{ p.installed ? '已安装' : '未安装' }}</span>
              </td>
              <td>
                <div class="ops">
                  <button
                    v-if="!p.installed"
                    type="button"
                    class="btn btn-primary btn-sm"
                    :disabled="!!installingPlugin"
                    @click="onTogglePlugin(p, true)"
                  >
                    {{ installingPlugin === p.name || installingPlugin === p.file ? '安装中…' : '安装' }}
                  </button>
                  <button
                    v-else
                    type="button"
                    class="btn btn-secondary btn-sm"
                    :disabled="!!installingPlugin"
                    @click="onTogglePlugin(p, false)"
                  >
                    卸载
                  </button>
                  <button type="button" class="btn btn-ghost btn-sm" @click="onEdit(p.file)">编辑</button>
                  <div class="export-menu relative">
                    <button type="button" class="btn btn-ghost btn-sm" @click.stop="toggleExportMenu(p.file)">导出</button>
                    <div v-if="exportMenu === p.file" class="menu-panel" @click.stop>
                      <button type="button" @click="doExport(p.file, 'zip')">ZIP（含 Skills）</button>
                      <button type="button" @click="doExport(p.file, 'yaml')">YAML（仅配置）</button>
                    </div>
                  </div>
                  <button type="button" class="btn btn-ghost btn-sm" title="发布到本地市场" @click="publishToMarketplace(p.file)">分享</button>
                </div>
              </td>
            </tr>
            <tr v-if="!filteredPlugins.length">
              <td colspan="7" class="empty-cell">
                {{ plugins.length ? '无匹配结果' : '暂无可用插件，点击「构建插件」或「导入」开始' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <Teleport to="body">
      <div class="float-bar" :class="{ show: selectedForExport.size > 0 }">
        <span>已选 {{ selectedForExport.size }} 个插件</span>
        <button type="button" class="btn btn-ghost btn-sm" @click="clearExportSelection">取消</button>
        <button type="button" class="btn btn-primary btn-sm" @click="exportSelectedPlugins">导出 ZIP</button>
      </div>
    </Teleport>

    <!-- 拖拽导入浮层 -->
    <Transition name="drop-fade">
      <div v-if="dragging" class="drop-overlay" @drop="onDrop" @dragover.prevent @dragleave.prevent>
        <div class="drop-card">
          <svg viewBox="0 0 24 24"><path d="M12 3v12"/><path d="m8 11 4 4 4-4"/><path d="M4 19h16"/></svg>
          <strong>松开导入插件</strong>
          <span>支持 .zip（含 Skills）或 .yaml / .yml</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.plugin-page {
  --green: #00b42a;
  --green-bg: #e8ffea;
  --amber: #ff7d00;
  --amber-bg: #fff7e8;
  --glow: 0 0 0 3px var(--primary-container-strong);
  --card: 0 1px 2px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding-bottom: 12px;
}

.plugin-head { margin: 0; }

.btn {
  height: 34px; padding: 0 12px; border-radius: 8px; font-size: 12px; font-weight: 600;
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  white-space: nowrap; border: 1px solid transparent; cursor: pointer;
  transition: background .18s ease, color .18s ease, border-color .18s ease;
  background: none; color: inherit; user-select: none;
}
.btn:disabled { opacity: .45; cursor: not-allowed; }
.btn-sm { height: 28px; padding: 0 10px; font-size: 11px; border-radius: 7px; }
.btn-primary { background: var(--primary); color: #fff; box-shadow: 0 1px 2px rgba(22, 93, 255, .22); }
.btn-primary:hover:not(:disabled) { background: var(--primary-hover); }
.btn-soft { background: var(--primary-container); color: var(--primary-hover); border-color: var(--primary-container-strong); }
.btn-soft:hover:not(:disabled) { background: #d9e6ff; }
.btn-secondary { background: var(--bg-elevated); color: var(--text-secondary); border-color: var(--border-base); }
.btn-secondary:hover:not(:disabled) { background: var(--bg-base); border-color: var(--border-strong); }
.btn-ghost { background: transparent; color: var(--text-secondary); }
.btn-ghost:hover:not(:disabled) { background: var(--bg-base); color: var(--text-primary); }
.btn:focus-visible { outline: none; box-shadow: var(--glow); }

.btn-cluster { display: inline-flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.btn-pair {
  display: inline-flex; border-radius: 8px; overflow: hidden;
  border: 1px solid var(--border-base); background: var(--bg-elevated);
}
.btn-pair .btn { border-radius: 0; border: none; height: 32px; border-right: 1px solid var(--border-base); }
.btn-pair .btn:last-child { border-right: none; }

.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.kpi {
  background: var(--bg-elevated); border-radius: 12px; padding: 16px 18px;
  box-shadow: var(--card);
  border: 1px solid rgba(0,0,0,.03); position: relative; overflow: hidden;
}
.kpi::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--border-strong); }
.kpi.live::before { background: var(--green); }
.kpi.warn::before { background: var(--amber); }
.kpi.brand::before { background: var(--primary); }
.kpi b { display: block; font-size: 22px; font-variant-numeric: tabular-nums; line-height: 1.1; color: var(--text-primary); }
.kpi span { font-size: 12px; color: var(--text-tertiary); }
.kpi em { font-style: normal; font-size: 11px; color: var(--text-tertiary); margin-top: 6px; display: block; }

.panel {
  background: var(--bg-elevated); border-radius: 14px;
  box-shadow: var(--card);
  border: 1px solid rgba(0,0,0,.03); overflow: hidden;
}
.toolbar {
  display: flex; justify-content: space-between; gap: 14px; flex-wrap: wrap;
  padding: 14px 18px; border-bottom: 1px solid var(--border-base); align-items: center;
}
.toolbar-left { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.search {
  display: flex; align-items: center; gap: 8px; height: 34px; padding: 0 12px;
  border: 1px solid var(--border-strong); border-radius: 8px; background: var(--bg-elevated); min-width: 220px;
}
.search:focus-within { border-color: var(--primary); box-shadow: var(--glow); }
.search input { border: none; outline: none; flex: 1; font-size: 12px; min-width: 0; background: transparent; }
.seg { display: inline-flex; background: var(--bg-base); padding: 3px; border-radius: 8px; }
.seg button {
  height: 28px; padding: 0 10px; border-radius: 6px; font-size: 12px; font-weight: 600;
  color: var(--text-tertiary); border: none; background: transparent; cursor: pointer;
}
.seg button.on { background: var(--bg-elevated); color: var(--primary-hover); box-shadow: 0 1px 2px rgba(0, 0, 0, .06); }

.table-wrap { overflow: visible; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th {
  text-align: left; font-size: 11px; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase;
  letter-spacing: .04em; padding: 11px 18px; background: var(--bg-base); border-bottom: 1px solid var(--border-base);
}
td { padding: 13px 18px; border-bottom: 1px solid #f7f8fa; vertical-align: middle; }
tr:hover td { background: var(--bg-base); }
tr.disabled td { opacity: .62; }

.pick { width: 16px; height: 16px; accent-color: var(--primary); cursor: pointer; }
.name { font-weight: 600; color: var(--text-primary); }
.ver {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 11px; color: var(--text-tertiary); margin-left: 8px; font-weight: 500;
}
.desc {
  font-size: 12.5px; color: var(--text-tertiary); line-height: 1.4;
  max-width: 360px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.num-cell {
  font-variant-numeric: tabular-nums; font-weight: 600; color: var(--text-secondary);
}
.status {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 11.5px; font-weight: 600; padding: 3px 9px; border-radius: 999px;
}
.status i { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.status.on { background: var(--green-bg); color: var(--green); }
.status.off { background: var(--amber-bg); color: var(--amber); }

.ops { display: flex; gap: 4px; flex-wrap: wrap; align-items: center; }

.export-menu { position: relative; }
.menu-panel {
  position: absolute; right: 0; top: calc(100% + 4px); min-width: 148px;
  background: var(--bg-elevated); border: 1px solid var(--border-base); border-radius: 10px; box-shadow: var(--card);
  z-index: 20; overflow: hidden;
}
.menu-panel button {
  display: block; width: 100%; text-align: left; padding: 9px 12px; border: none; background: none;
  font-size: 12px; color: var(--text-secondary); cursor: pointer;
}
.menu-panel button:hover { background: var(--primary-container); color: var(--primary-hover); }

.empty-cell {
  text-align: center; color: var(--text-tertiary); font-size: 12.5px; padding: 28px 0;
}

.float-bar {
  position: fixed; left: 50%; bottom: 22px; transform: translateX(-50%) translateY(20px);
  background: var(--text-primary); color: #fff; border-radius: 14px; padding: 10px 12px 10px 16px;
  display: flex; align-items: center; gap: 12px; box-shadow: 0 10px 30px rgba(0, 0, 0, .22);
  opacity: 0; pointer-events: none; transition: .2s ease; z-index: 40; max-width: calc(100vw - 32px);
}
.float-bar.show { opacity: 1; transform: translateX(-50%) translateY(0); pointer-events: auto; }
.float-bar span { font-size: 12.5px; white-space: nowrap; }
.float-bar .btn { height: 30px; color: #fff; border-color: rgba(255, 255, 255, .2); }
.float-bar .btn-primary { background: var(--primary); border-color: transparent; }
.float-bar .btn-ghost:hover:not(:disabled) { background: rgba(255, 255, 255, .1); color: #fff; }

/* 拖拽导入浮层 */
.drop-overlay {
  position: fixed; inset: 0; z-index: 50;
  background: rgba(22, 93, 255, .08);
  backdrop-filter: blur(2px);
  display: grid; place-items: center;
  pointer-events: auto;
}
.drop-card {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 32px 48px;
  border: 2px dashed var(--primary);
  border-radius: 18px;
  background: var(--bg-elevated);
  color: var(--primary-hover);
  text-align: center;
  box-shadow: 0 12px 40px rgba(22, 93, 255, .18);
}
.drop-card svg { width: 36px; height: 36px; stroke: currentColor; fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.drop-card strong { font-size: 15px; }
.drop-card span { font-size: 12px; color: var(--text-tertiary); }
.drop-fade-enter-active, .drop-fade-leave-active { transition: opacity .18s ease; }
.drop-fade-enter-from, .drop-fade-leave-to { opacity: 0; }

@media (max-width: 960px) {
  .kpis { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 620px) {
  .kpis { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  .btn, .float-bar { transition: none !important; }
}
</style>
