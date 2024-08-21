export class BinaryPacker {
	static pack(number: number, bit1: boolean) {
		if (number < 0 || number > 999999) {
			throw new Error('Number must be between 0 and 999999');
		}

		const buffer = new ArrayBuffer(3);
		const view = new Uint8Array(buffer);

		// Pack the number (20 bits)
		view[0] = (number >> 12) & 0xff;
		view[1] = (number >> 4) & 0xff;
		view[2] = (number & 0x0f) << 4;

		// Pack the single bit
		view[2] |= bit1 ? 0x01 : 0;

		return buffer;
	}

	static unpack(buffer: ArrayBuffer) {
		const view = new Uint8Array(buffer);

		// Unpack the number
		const number = (view[0] << 12) | (view[1] << 4) | (view[2] >> 4);

		// Unpack the single bit
		const bit1 = !!(view[2] & 0x01);

		return { number, bit1 };
	}
}
