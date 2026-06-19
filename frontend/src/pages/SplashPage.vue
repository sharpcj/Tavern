<template>
  <div class="splash" @click="handleClick">
    <div class="splash-overlay" />
    <div class="splash-content">
      <div class="splash-icon">
        <span class="splash-icon-text">🏫</span>
      </div>
      <h1 class="splash-title">
        <span
          v-for="(char, i) in titleChars"
          :key="i"
          class="splash-char"
          :style="{ animationDelay: `${0.08 * i}s` }"
        >{{ char }}</span>
      </h1>
      <p class="splash-subtitle">同窗岁月 · 青春再续</p>
      <p class="splash-hint">{{ hintText }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const titleChars = ref<string[]>([])
const fullTitle = '松滋一中2010届高三4班社区'

titleChars.value = fullTitle.split('')

const hintText = ref('点击任意位置开始')
let audio: HTMLAudioElement | null = null
let audioStarted = false

function goHome() {
  router.replace('/home')
}

function startAudio() {
  if (audioStarted) return
  audioStarted = true
  hintText.value = '点击任意位置跳过'
  audio = new Audio('/intro.wav')
  audio.play().catch(() => {
    // 播放失败（极少情况），仍可点击跳过
  })
  audio.addEventListener('ended', goHome)
}

function skip() {
  if (audio) {
    audio.pause()
    audio.currentTime = 0
  }
  goHome()
}

function handleClick() {
  if (!audioStarted) {
    startAudio()
  } else {
    skip()
  }
}

onMounted(() => {
  // 尝试自动播放（现代浏览器通常阻止），成功则直接开始
  audio = new Audio('/intro.wav')
  audio.play().then(() => {
    audioStarted = true
    hintText.value = '点击任意位置跳过'
    audio!.addEventListener('ended', goHome)
  }).catch(() => {
    // 自动播放被阻止，等待用户首次点击
    audio = null
  })
})

onUnmounted(() => {
  if (audio) {
    audio.pause()
    audio.removeEventListener('ended', goHome)
    audio = null
  }
})
</script>

<style scoped>
.splash {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(255, 215, 0, 0.08) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 80%, rgba(100, 149, 237, 0.06) 0%, transparent 60%),
    linear-gradient(135deg, #0f172a 0%, #1a2332 40%, #1e3a5f 100%);
  overflow: hidden;
  user-select: none;
}

.splash-overlay {
  position: absolute;
  inset: 0;
  background:
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(255, 255, 255, 0.008) 2px,
      rgba(255, 255, 255, 0.008) 4px
    );
  pointer-events: none;
}

.splash-content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 2rem;
}

.splash-icon {
  margin-bottom: 1.5rem;
}

.splash-icon-text {
  font-size: 3.5rem;
  display: inline-block;
  animation: iconFloat 3s ease-in-out infinite;
}

@keyframes iconFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}

.splash-title {
  font-size: clamp(1.6rem, 5vw, 2.8rem);
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: 0.08em;
  margin: 0 0 1rem;
  line-height: 1.6;
}

.splash-char {
  display: inline-block;
  opacity: 0;
  animation: charFadeIn 0.6s ease-out forwards;
  text-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
}

@keyframes charFadeIn {
  0% {
    opacity: 0;
    transform: translateY(24px);
    filter: blur(4px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
    filter: blur(0);
  }
}

.splash-subtitle {
  font-size: 1rem;
  color: rgba(203, 213, 225, 0.7);
  margin: 0 0 2rem;
  letter-spacing: 0.4em;
  animation: subtitleIn 1s ease-out 1.5s both;
}

@keyframes subtitleIn {
  0% {
    opacity: 0;
    transform: translateY(8px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.splash-hint {
  font-size: 0.85rem;
  color: rgba(148, 163, 184, 0.5);
  margin: 0;
  animation: hintPulse 2s ease-in-out infinite;
}

@keyframes hintPulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}
</style>
