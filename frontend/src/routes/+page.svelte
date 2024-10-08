<script lang="ts">
	import { BinaryPacker } from '$lib/binary';
	import config from '$lib/config-public';

	const SIZE = 10000;
	const COLS = 100;

	let checkboxes = $state(Array(SIZE).fill(false));
	let socket: WebSocket;
	let updateQueue: MessageEvent[] = [];
	let isProcessing = false;

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

	function processQueue() {
		if (updateQueue.length > 0) {
			// Process only the last message
			const lastMessage = updateQueue[updateQueue.length - 1];
			processMessage(lastMessage);
			updateQueue = []; // Clear the queue after processing

			// Schedule next check
			setTimeout(processQueue, 16); // Limit updates to max ~60 times per second
		} else {
			isProcessing = false;
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
			updateQueue.push(event);
			if (!isProcessing) {
				isProcessing = true;
				setTimeout(processQueue, 0);
			}
		};

		// TODO: receive diffs
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
