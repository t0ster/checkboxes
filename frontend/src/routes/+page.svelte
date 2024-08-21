<script lang="ts">
	import { BinaryPacker } from './lib';
	import config from '$lib/config-public';

	const SIZE = 10000;
	const COLS = 100;

	let checkboxes = $state(Array(SIZE).fill(false));
	let socket: WebSocket;

	function connectWebSocket() {
		socket = new WebSocket(config.PUBLIC_API_WS);
		socket.binaryType = 'arraybuffer';

		socket.onclose = () => {
			console.log('WebSocket connection closed. Reconnecting...');
			setTimeout(connectWebSocket, 1000);
		};

		// TODO: receive diffs
		socket.onmessage = (event) => {
			const buffer = event.data as ArrayBuffer;
			const view = new Uint8Array(buffer);

			for (let i = 0; i < SIZE; i++) {
				const byteIndex = Math.floor(i / 8);
				const bitIndex = i % 8;
				checkboxes[i] = !!(view[byteIndex] & (1 << (7 - bitIndex)));
			}
		};
	}

	$effect(() => {
		connectWebSocket();
	});

	function onChange(index: number) {
		const packed = BinaryPacker.pack(index, checkboxes[index]);
		if (socket.readyState === WebSocket.OPEN) {
			socket.send(packed);
		} else {
			console.log('WebSocket connection not open. Cannot send message.');
		}
	}
</script>

<div class="flex h-screen items-center justify-center">
	<div class="aspect-square h-full p-1">
		<div
			class="grid h-full w-full gap-0 border-[0.1px] border-zinc-700"
			style={`grid-template-columns: repeat(${COLS}, minmax(0, 1fr));`}
		>
			{#each { length: SIZE } as _, i}
				<input
					id={`checkbox-${i}`}
					type="checkbox"
					class="h-full w-full appearance-none border-[0.1px] border-zinc-700 checked:bg-white"
					bind:checked={checkboxes[i]}
					onchange={() => onChange(i)}
				/>
			{/each}
		</div>
	</div>
</div>
