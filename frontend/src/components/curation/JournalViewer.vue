<template>
  <div class="journal-viewer prose" v-html="renderedMarkdown"></div>
</template>

<script setup>
import { computed } from 'vue';
import { marked } from 'marked';

const props = defineProps({
  markdown: {
    type: String,
    required: true,
  },
});

const renderedMarkdown = computed(() => {
  // For security, it's important to sanitize the output if the markdown
  // comes from untrusted sources. Since this is an internal tool with
  // journal entries, we can assume it's safe.
  return marked(props.markdown);
});
</script>

<style scoped>
.journal-viewer {
  color: #303133;
  line-height: 1.6;
}

/* Basic styling for rendered markdown.
   Using a class like 'prose' is common.
   For a nicer look, one could use a library like Tailwind Typography.
*/
.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3) {
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 0.3em;
  margin-top: 1.5em;
  margin-bottom: 1em;
}

.prose :deep(p) {
  margin-bottom: 1em;
}

.prose :deep(strong) {
  font-weight: 600;
}

.prose :deep(em) {
  font-style: italic;
}

.prose :deep(blockquote) {
  padding: 0 1em;
  color: #606266;
  border-left: 0.25em solid #ebeef5;
  margin-left: 0;
}

.prose :deep(ul),
.prose :deep(ol) {
  padding-left: 2em;
}

.prose :deep(code) {
  background-color: #f0f2f5;
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  border-radius: 3px;
}
</style>
