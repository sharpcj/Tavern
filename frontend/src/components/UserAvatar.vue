<template>
  <el-avatar :size="size" :src="src || undefined" class="user-avatar">
    <svg class="user-avatar-fallback" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 12.25c2.35 0 4.25-1.9 4.25-4.25S14.35 3.75 12 3.75 7.75 5.65 7.75 8s1.9 4.25 4.25 4.25Zm0 2c-3.35 0-6.25 1.72-6.25 3.85v.65c0 .83.67 1.5 1.5 1.5h9.5c.83 0 1.5-.67 1.5-1.5v-.65c0-2.13-2.9-3.85-6.25-3.85Z" />
    </svg>
  </el-avatar>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  src?: string
  size?: number
}>(), {
  src: '',
  size: 40,
})
</script>

<style scoped>
.user-avatar {
  background: #e5e7eb;
  color: #6b7280;
}
.user-avatar-fallback {
  width: 62%;
  height: 62%;
  fill: currentColor;
}
</style>
