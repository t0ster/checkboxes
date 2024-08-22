<script>
	import '../app.css';

	const commitHash = import.meta.env.VITE_CF_PAGES_COMMIT_SHA || 'Development';
</script>

<slot></slot>

<div class="absolute bottom-0 right-2 p-2 text-center text-xs text-gray-500">
	Commit: {commitHash.slice(0, 7)}
</div>
