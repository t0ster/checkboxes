<script>
	import '../app.css';
	import commitHash from '$lib/commit';
</script>

<slot></slot>

<div class="absolute bottom-0 right-2 p-2 text-center text-xs text-gray-500">
	Commit: {commitHash.slice(0, 7)}
</div>
