
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
  spans: {
    type: Array,
    default: () => [],
  },
});

window.highlightMaybe = function($element) {
  // highlight all elements with the same crossmark-N class
  const classes = $element.className.split(' ');
  console.log('highlightMaybe', classes);
  $element.classList.add('highlighted-hover');
  for (const cls of classes) {
    if (cls.startsWith('crossmark-')) {
      const els = document.getElementsByClassName(cls);
      for (const el of els) {
        if (el !== $element) 
          el.classList.add('highlighted-hover');
      }
    }
  }
}

window.unhighlight = function($element) {
  // highlight all elements with the same crossmark-N class
  const classes = $element.className.split(' ');
  console.log('highlightMaybe', classes);
  $element.classList.remove('highlighted-hover');
  for (const cls of classes) {
    if (cls.startsWith('crossmark-')) {
      const els = document.getElementsByClassName(cls);
      for (const el of els) {
        if (el !== $element) 
          el.classList.remove('highlighted-hover');
      }
    }
  }
}

const renderedMarkdown = computed(() => {
  const spans = props.spans;
  if (!spans || !Array.isArray(spans) || spans.length === 0) return marked(props.markdown);

  // Find all paragraph breaks (\n\n)
  const paraBreaks = [];
  let idx = 0;
  while ((idx = props.markdown.indexOf('\n\n', idx)) !== -1) {
    paraBreaks.push(idx);
    idx += 2;
  }
  // Add end of text as a "break"
  paraBreaks.push(props.markdown.length);

  // Sort spans by start ascending
  const sortedSpans = [...spans].sort((a, b) => a.start - b.start);
  let result = '';
  let lastIdx = 0;
  let skips = 1;
  for (const span of sortedSpans) {
    let start = Math.max(0, Math.min(props.markdown.length, span.start));
    let end = Math.max(start, Math.min(props.markdown.length, span.end));

    // Find paragraph breaks within this span
    const breaksInSpan = paraBreaks.filter(b => b > start && b < end);
    
    if (breaksInSpan.length === 0) {
      // Span is within a single paragraph
      result += props.markdown.slice(lastIdx, start);
      result += `<mark class="highlighted" onmouseover="highlightMaybe(this)" onmouseleave="unhighlight(this)">` + props.markdown.slice(start, end) + '</mark>';
      lastIdx = end;
    } else {
      // Span crosses paragraph(s)
      let segStart = start;
      for (const b of breaksInSpan) {
        // Mark up to the break
        result += props.markdown.slice(lastIdx, segStart);
        result += `<mark class="highlighted crossmark-${skips}" onmouseover="highlightMaybe(this)" onmouseleave="unhighlight(this)">` + props.markdown.slice(segStart, b) + '</mark>';
        // Add the paragraph break itself ("\n\n")
        result += props.markdown.slice(b, b + 2);
        lastIdx = b + 2;
        segStart = b + 2;
      }
      // Final segment after last break
      if (segStart < end) {
        result += props.markdown.slice(lastIdx, segStart);
        result += `<mark class="highlighted crossmark-${skips}" onmouseover="highlightMaybe(this)" onmouseleave="unhighlight(this)">` + props.markdown.slice(segStart, end) + '</mark>';
        lastIdx = end;
      }
      skips += 1;
    }
  }
  result += props.markdown.slice(lastIdx);
  // For security, it's important to sanitize the output if the markdown
  // comes from untrusted sources. Since this is an internal tool with
  // journal entries, we can assume it's safe.
  return marked(result);
});
</script>

<style scoped>
  .highlighted {
    background: yellow;
  }

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
