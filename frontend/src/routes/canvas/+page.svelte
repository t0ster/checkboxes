<script lang="ts">
	import { BinaryPacker } from '$lib/binary';
	import config from '$lib/config-public';

	const SIZE = 10000;
	const COLS = 100;
	const ROWS = SIZE / COLS;
	const CELL_SIZE = 10; // Adjust this value to change the size of each cell

	let cellCanvas: HTMLCanvasElement;
	let gridCanvas: HTMLCanvasElement;
	let cellCtx: CanvasRenderingContext2D;
	let gridCtx: CanvasRenderingContext2D;
	let cells = new Uint8Array(SIZE);
	let socket: WebSocket;
	let updateQueue: MessageEvent[] = [];
	let isProcessing = false;
	let isDrawing = false;
	let lastCellIndex = -1;
	let initialCellState = 0;

	$effect(() => {
		cellCtx = cellCanvas.getContext('2d')!;
		gridCtx = gridCanvas.getContext('2d')!;
		cellCanvas.width = gridCanvas.width = COLS * CELL_SIZE;
		cellCanvas.height = gridCanvas.height = ROWS * CELL_SIZE;
		drawAllCells();
		drawGrid();
		connectWebSocket();
	});

	function drawGrid() {
		gridCtx.strokeStyle = '#52525b'; // zinc-600
		gridCtx.lineWidth = 0.5; // Thin lines for the grid

		for (let x = 0; x <= COLS; x++) {
			gridCtx.beginPath();
			gridCtx.moveTo(x * CELL_SIZE, 0);
			gridCtx.lineTo(x * CELL_SIZE, gridCanvas.height);
			gridCtx.stroke();
		}
		for (let y = 0; y <= ROWS; y++) {
			gridCtx.beginPath();
			gridCtx.moveTo(0, y * CELL_SIZE);
			gridCtx.lineTo(gridCanvas.width, y * CELL_SIZE);
			gridCtx.stroke();
		}
	}

	function drawAllCells() {
		for (let i = 0; i < SIZE; i++) {
			drawCell(i);
		}
	}

	function drawCell(index: number) {
		const x = (index % COLS) * CELL_SIZE;
		const y = Math.floor(index / COLS) * CELL_SIZE;
		cellCtx.fillStyle = cells[index] ? 'white' : 'black';
		cellCtx.fillRect(x, y, CELL_SIZE, CELL_SIZE);
	}

	function processMessage(event: MessageEvent) {
		const buffer = event.data as ArrayBuffer;
		const view = new Uint8Array(buffer);

		for (let i = 0; i < SIZE; i++) {
			const byteIndex = Math.floor(i / 8);
			const bitIndex = i % 8;
			const newState = !!(view[byteIndex] & (1 << (7 - bitIndex)));
			if (!!cells[i] !== newState) {
				cells[i] = newState ? 1 : 0;
				drawCell(i);
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

	function startDrawing(event: MouseEvent) {
		isDrawing = true;
		const index = getCellIndex(event);
		initialCellState = cells[index];
		draw(event);
	}

	function stopDrawing() {
		isDrawing = false;
		lastCellIndex = -1;
	}

	function getCellIndex(event: MouseEvent): number {
		const rect = cellCanvas.getBoundingClientRect();
		const x = Math.floor((event.clientX - rect.left) / CELL_SIZE);
		const y = Math.floor((event.clientY - rect.top) / CELL_SIZE);
		return y * COLS + x;
	}

	function draw(event: MouseEvent) {
		if (!isDrawing) return;

		const index = getCellIndex(event);

		if (index >= 0 && index < SIZE && index !== lastCellIndex) {
			if (cells[index] === initialCellState) {
				cells[index] = initialCellState ? 0 : 1;
				drawCell(index);

				const packed = BinaryPacker.pack(index, !!cells[index]);
				if (socket.readyState === WebSocket.OPEN) {
					socket.send(packed);
				} else {
					console.log('WebSocket connection not open. Cannot send message.');
				}
			}
			lastCellIndex = index;
		}
	}
</script>

<div class="relative flex h-screen items-center justify-center">
	<canvas
		bind:this={cellCanvas}
		onmousedown={startDrawing}
		onmousemove={draw}
		onmouseup={stopDrawing}
		onmouseleave={stopDrawing}
		class="absolute"
	></canvas>
	<canvas bind:this={gridCanvas} class="pointer-events-none absolute"></canvas>
</div>
