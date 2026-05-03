<!-- Test fixture: throws on render so ErrorBoundary tests can verify catch + fallback. -->
<script lang="ts">
  throw new Error('boom');
</script>
