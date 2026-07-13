<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useRulesStore } from '../stores/rules'
const rules = useRulesStore()
const { groupedRules, selectedRulePath, editingContent, editingMeta, dirty, selectedRule } = storeToRefs(rules)
const { loadRules, selectRule, onContentChange, saveRule, deleteRule, newRule, syncRules, exportRules, importRules } = rules
const inputRef = ref<HTMLInputElement | null>(null)
function triggerImport() { inputRef.value?.click() }
onMounted(() => { loadRules() })
</script>

<template>
  <div class="space-y-3">
    <div class="bg-white rounded-xl shadow-card p-4">
      <!-- 工具栏 -->
      <div class="flex items-center justify-between mb-3 pb-2 border-b border-gray-100">
        <h3 class="text-sm font-semibold flex items-center gap-2">
          <span class="w-1 h-4 bg-brand-500 rounded"></span>Rules 管理
          <span class="text-[10px] text-ink-500 font-normal">{{ rules.rules.length }} 个规则</span>
          <span v-if="dirty" class="text-[10px] text-orange-500 font-normal">● 未保存</span>
        </h3>
        <div class="flex items-center gap-2">
          <button @click="newRule" class="text-[11px] text-brand-600 hover:underline">新建</button>
          <button @click="saveRule" :disabled="!selectedRulePath" class="text-[11px] text-brand-600 hover:underline disabled:text-ink-300">保存</button>
          <button @click="syncRules" class="text-[11px] text-brand-600 hover:underline">同步到 IDE</button>
          <button @click="exportRules" class="text-[11px] text-ink-600 hover:text-brand-600">导出</button>
          <button @click="triggerImport" class="text-[11px] text-brand-600 hover:underline">导入</button>
          <input ref="inputRef" type="file" accept=".zip,.md" @change="importRules" class="hidden">
        </div>
      </div>

      <div class="flex gap-4">
        <!-- 左侧：规则列表 -->
        <div class="w-64 flex-shrink-0 max-h-[600px] overflow-y-auto">
          <div v-for="(items, cat) in groupedRules" :key="cat" class="mb-3">
            <div class="text-[10px] font-semibold text-ink-400 uppercase tracking-wide mb-1 px-2">{{ cat }}</div>
            <div
              v-for="r in items"
              :key="r.path"
              @click="selectRule(r.path)"
              :class="['cursor-pointer rounded-lg px-2 py-1.5 mb-0.5 transition text-xs',
                       selectedRulePath === r.path ? 'bg-brand-50 text-brand-700' : 'hover:bg-gray-50 text-ink-700']"
            >
              <div class="flex items-center gap-1.5">
                <span class="font-medium truncate flex-1">{{ r.name }}</span>
                <span v-if="r.alwaysApply" class="text-[9px] bg-green-100 text-green-600 px-1 rounded">always</span>
                <span v-if="r.source === 'template'" class="text-[9px] text-ink-400">预置</span>
                <span v-else class="text-[9px] text-brand-400">自定义</span>
              </div>
              <div v-if="r.description" class="text-[10px] text-ink-400 truncate mt-0.5">{{ r.description }}</div>
            </div>
          </div>
          <div v-if="!rules.rules.length" class="text-center text-ink-500 text-xs py-6">暂无规则</div>
        </div>

        <!-- 右侧：编辑器 -->
        <div class="flex-1 min-w-0">
          <div v-if="selectedRulePath">
            <!-- frontmatter 字段 -->
            <div class="grid grid-cols-2 gap-3 mb-3 p-3 bg-gray-50 rounded-lg">
              <div>
                <label class="text-[10px] text-ink-500 block mb-0.5">description（描述何时使用此规则）</label>
                <input v-model="editingMeta.description" @input="onContentChange"
                       class="w-full text-xs border border-gray-200 rounded px-2 py-1 focus:border-brand-400 focus:outline-none"
                       placeholder="编写后端代码时使用此规则">
              </div>
              <div>
                <label class="text-[10px] text-ink-500 block mb-0.5">globs（文件匹配模式，逗号分隔）</label>
                <input v-model="editingMeta.globs" @input="onContentChange"
                       class="w-full text-xs border border-gray-200 rounded px-2 py-1 focus:border-brand-400 focus:outline-none"
                       placeholder="**/*.java,**/*.py">
              </div>
              <div class="flex items-center gap-4">
                <label class="flex items-center gap-1.5 text-xs text-ink-600 cursor-pointer">
                  <input type="checkbox" v-model="editingMeta.alwaysApply" @change="onContentChange"
                         class="w-3.5 h-3.5 accent-brand-500">
                  alwaysApply（始终生效）
                </label>
                <div class="flex-1">
                  <label class="text-[10px] text-ink-500 block mb-0.5">scene（场景，如 git_message）</label>
                  <input v-model="editingMeta.scene" @input="onContentChange"
                         class="w-full text-xs border border-gray-200 rounded px-2 py-1 focus:border-brand-400 focus:outline-none"
                         placeholder="">
                </div>
              </div>
            </div>

            <!-- 正文编辑器 -->
            <div class="flex items-center justify-between mb-1">
              <span class="text-[10px] text-ink-400">规则正文（Markdown）</span>
              <div class="flex gap-2">
                <button v-if="selectedRule?.source !== 'template'" @click="deleteRule(selectedRulePath)"
                        class="text-[10px] text-red-500 hover:underline">删除</button>
              </div>
            </div>
            <textarea
              v-model="editingContent"
              @input="onContentChange"
              class="w-full h-[400px] text-xs font-mono border border-gray-200 rounded-lg p-3 focus:border-brand-400 focus:outline-none resize-none"
              placeholder="在此编写规则内容..."
              spellcheck="false"
            ></textarea>
          </div>
          <div v-else class="flex items-center justify-center h-[500px] text-ink-400 text-xs">
            ← 从左侧选择一个规则，或点击「新建」
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
