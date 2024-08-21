<script lang="ts">
	import { BinaryPacker } from './lib';
	import config from '$lib/config-public';

	const SIZE = 10000;
	const COLS = 100;
	const UPDATE_FREQUENCY = 50;

	let checkboxes = $state(Array(SIZE).fill(false));
	let socket: WebSocket;
	let lastUpdateTime = 0;
	let pendingUpdate: MessageEvent | null = null;

	function processMessage(event: MessageEvent) {
		const buffer = event.data as ArrayBuffer;
		const view = new Uint8Array(buffer);

		for (let i = 0; i < SIZE; i++) {
			const byteIndex = Math.floor(i / 8);
			const bitIndex = i % 8;
			const newState = !!(view[byteIndex] & (1 << (7 - bitIndex)));
			if (checkboxes[i] !== newState) {
				checkboxes[i] = newState;
			}
		}
	}

	function connectWebSocket() {
		socket = new WebSocket(config.PUBLIC_API_WS);
		socket.binaryType = 'arraybuffer';

		socket.onclose = () => {
			console.log('WebSocket connection closed. Reconnecting...');
			setTimeout(connectWebSocket, 1000);
		};

		socket.onmessage = (event: MessageEvent) => {
			const currentTime = Date.now();
			if (currentTime - lastUpdateTime < UPDATE_FREQUENCY) {
				// Store this message as pending
				pendingUpdate = event;
				if (!lastUpdateTime) {
					// If this is the first message, schedule an update
					setTimeout(checkPendingUpdate, UPDATE_FREQUENCY);
				}
			} else {
				// Process the message immediately
				processMessage(event);
				lastUpdateTime = currentTime;
			}
		};

		// TODO: receive diffs
	}

	$effect(() => {
		connectWebSocket();
	});

	function checkPendingUpdate() {
		const currentTime = Date.now();
		if (pendingUpdate && currentTime - lastUpdateTime >= UPDATE_FREQUENCY) {
			processMessage(pendingUpdate);
			lastUpdateTime = currentTime;
			pendingUpdate = null;
		}
		if (pendingUpdate) {
			// If there's still a pending update, check again after the remaining time
			setTimeout(checkPendingUpdate, UPDATE_FREQUENCY - (currentTime - lastUpdateTime));
		}
	}

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
