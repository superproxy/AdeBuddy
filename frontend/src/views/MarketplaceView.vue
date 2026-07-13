<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useMarketplaceStore } from '../stores/marketplace'

const mkt = useMarketplaceStore()
const { items, loading, searchQuery, installing } = storeToRefs(mkt)

let searchTimer: ReturnType<typeof setTimeout> | null = null

function onSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => mkt.browse(), 300)
}

function formatSize(bytes: number): string {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatDate(iso: string): string {
  if (!iso) return '-'
  try {
    return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
  } catch {
    return iso
  }
}

onMounted(() => { mkt.browse() })
</script>

<template>
  <div class="space-y-3">
    <div class="bg-white rounded-xl shadow-card p-4">
      <!-- 标题栏 -->
      <div class="flex items-center justify-between mb-4 pb-3 border-b border-gray-100">
        <h3 class="text-sm font-semibold flex items-center gap-2">
          <span class="w-1 h-4 bg-brand-500 rounded"></span>插件市场
          <span class="text-[10px] text-ink-500 font-normal">{{ items.length }} 个</span>
        </h3>
        <button @click="mkt.browse()" :disabled="loading"
               class="text-[11px] text-brand-600 hover:underline disabled:opacity-50">
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>

      <!-- 搜索框 -->
      <div class="mb-4">
        <div class="relative">
          <input
            v-model="searchQuery"
            @input="onSearch"
            @keyup.enter="mkt.browse()"
            type="text"
            placeholder="搜索插件名称、描述、标签…"
            class="w-full px-3 py-2 pl-9 text-xs border border-ink-300 rounded-lg focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          />
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      <!-- 卡片列表 -->
      <div v-if="loading && !items.length" class="text-center text-ink-500 text-xs py-12">
        加载中…
      </div>
      <div v-else-if="!items.length" class="text-center text-ink-500 text-xs py-12">
        <div class="mb-2">📦</div>
        <p>市场暂无插件</p>
        <p class="mt-1 text-[10px] text-ink-400">在「插件配置」页点击「分享到市场」即可发布</p>
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        <div
          v-for="item in items"
          :key="item.id"
          class="border border-ink-300 rounded-lg p-3 hover:border-brand-500 hover:shadow-sm transition flex flex-col gap-2"
        >
          <!-- 标题行 -->
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5">
                <span class="font-medium text-xs text-ink-900 truncate">{{ item.name }}</span>
                <span class="text-[10px] text-ink-500 flex-shrink-0">v{{ item.version }}</span>
              </div>
              <div class="text-[11px] text-ink-500 line-clamp-2 mt-0.5">{{ item.description || '无描述' }}</div>
            </div>
          </div>

          <!-- 标签 -->
          <div v-if="item.tags?.length" class="flex flex-wrap gap-1">
            <span
              v-for="tag in item.tags"
              :key="tag"
              class="px-1.5 py-0.5 bg-brand-50 text-brand-600 rounded text-[10px]"
            >{{ tag }}</span>
          </div>

          <!-- 元信息 -->
          <div class="flex items-center gap-2 text-[10px] text-ink-400">
            <span>{{ item.author }}</span>
            <span>·</span>
            <span>{{ formatSize(item.size) }}</span>
            <span>·</span>
            <span>⬇ {{ item.downloads || 0 }}</span>
            <span>·</span>
            <span>{{ formatDate(item.published_at) }}</span>
          </div>

          <!-- 操作按钮 -->
          <div class="flex items-center gap-2 mt-auto pt-1">
            <button
              @click="mkt.install(item.id)"
              :disabled="installing === item.id || !!installing"
              class="text-[10px] px-2 py-1 bg-brand-500 text-white rounded hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {{ installing === item.id ? '安装中…' : '安装' }}
            </button>
            <a
              :href="'/api/marketplace/download?id=' + encodeURIComponent(item.id)"
              class="text-[10px] px-2 py-1 border border-ink-300 text-ink-600 rounded hover:border-brand-500 hover:text-brand-600 transition"
            >下载</a>
            <button
              @click="mkt.remove(item.id)"
              class="text-[10px] px-2 py-1 text-red-400 hover:text-red-600 transition ml-auto"
            >移除</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
