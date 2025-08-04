#include <stdio.h>
#include <stdint.h>

const unsigned short LUT[256] = {
    0x0000,
    0x0100,
    0x0200,
    0x0300,
    0x0400,
    0x0500,
    0x0600,
    0x0000,
    0x0800,
    0x0900,
    0x0A00,
    0x0000,
    0x0C00,
    0x4080,
    0x0000,
    0x0050,
    0x1000,
    0x1100,
    0x1200,
    0x4020,
    0x1400,
    0x2002,
    0x0000,
    0x0000,
    0x1800,
    0x0000,
    0x8001,
    0x0000,
    0x0000,
    0x0000,
    0x00A0,
    0x0000,
    0x2000,
    0x2100,
    0x2200,
    0x0000,
    0x2400,
    0x1002,
    0x8040,
    0x0084,
    0x2800,
    0x8010,
    0x4004,
    0x0000,
    0x0000,
    0x0000,
    0x0000,
    0x0000,
    0x3000,
    0x0402,
    0x0000,
    0x0011,
    0x0102,
    0x0002,
    0x0000,
    0x0202,
    0x0000,
    0x0024,
    0x0000,
    0x0000,
    0x0041,
    0x0802,
    0x0000,
    0x0000,
    0x4000,
    0x4100,
    0x4200,
    0x1020,
    0x4400,
    0x0880,
    0x0000,
    0x0000,
    0x4800,
    0x0480,
    0x2004,
    0x0000,
    0x0180,
    0x0080,
    0x0009,
    0x0280,
    0x5000,
    0x0220,
    0x0120,
    0x0020,
    0x8008,
    0x0000,
    0x0000,
    0x0420,
    0x0000,
    0x0000,
    0x0000,
    0x0820,
    0x0000,
    0x1080,
    0x0000,
    0x0006,
    0x6000,
    0x0000,
    0x0804,
    0x0000,
    0x0000,
    0x0000,
    0x0022,
    0x0000,
    0x0204,
    0x0000,
    0x0004,
    0x0104,
    0x0000,
    0x2080,
    0x0404,
    0x0000,
    0x0000,
    0x0000,
    0x0048,
    0x2020,
    0x0000,
    0x4002,
    0x0000,
    0x0000,
    0x0082,
    0x0000,
    0x1004,
    0x0000,
    0x0000,
    0x0018,
    0x0000,
    0x0000,
    0x8000,
    0x8100,
    0x8200,
    0x0000,
    0x8400,
    0x0000,
    0x2040,
    0x0028,
    0x8800,
    0x2010,
    0x1001,
    0x0000,
    0x0000,
    0x0000,
    0x0000,
    0x0000,
    0x9000,
    0x0000,
    0x0801,
    0x0042,
    0x4008,
    0x0000,
    0x0000,
    0x0000,
    0x0201,
    0x0088,
    0x0001,
    0x0101,
    0x0012,
    0x0000,
    0x0401,
    0x0000,
    0xA000,
    0x0810,
    0x0440,
    0x0000,
    0x0240,
    0x0000,
    0x0040,
    0x0140,
    0x0110,
    0x0010,
    0x0000,
    0x0210,
    0x0000,
    0x0410,
    0x0840,
    0x0003,
    0x0000,
    0x0000,
    0x0000,
    0x0000,
    0x0000,
    0x8002,
    0x1040,
    0x0000,
    0x0000,
    0x1010,
    0x2001,
    0x0000,
    0x0000,
    0x0000,
    0x000C,
    0x0000,
    0xC000,
    0x0000,
    0x0000,
    0x0014,
    0x1008,
    0x0000,
    0x0000,
    0x0000,
    0x0000,
    0x0021,
    0x0000,
    0x0000,
    0x0044,
    0x8080,
    0x0000,
    0x0000,
    0x0408,
    0x0000,
    0x0000,
    0x8020,
    0x0008,
    0x0108,
    0x0208,
    0x0081,
    0x0000,
    0x0000,
    0x4001,
    0x0000,
    0x0808,
    0x0000,
    0x0000,
    0x0000,
    0x0000,
    0x000A,
    0x0000,
    0x0000,
    0x0090,
    0x0000,
    0x4040,
    0x0000,
    0x0000,
    0x4010,
    0x8004,
    0x00C0,
    0x0000,
    0x0000,
    0x0000,
    0x0000,
    0x0005,
    0x0000,
    0x0000,
    0x0000,
    0x2008,
    0x0060,
    0x0000,
    0x0000,
    0x0000,
    0x0000,
    0x0030,
    0x0000,
    0x0000,
    0x0000,
    0x0000,
    0x0000,
};

const unsigned char parity_matrix[8] = {
    0b01001101,
    0b10100110,
    0b01010011,
    0b10101001,
    0b11010100,
    0b01101010,
    0b00110101,
    0b10011010
};

// H matrix as unsigned short[8], each row is 16 bits: [I | P^T]
const unsigned short H[8] = {
    0b10000000_01011001, // 0x8059
    0b01000000_10101100, // 0x40AC
    0b00100000_01010110, // 0x2056
    0b00010000_00101011, // 0x102B
    0b00001000_10010101, // 0x0895
    0b00000100_11001010, // 0x04CA
    0b00000010_01100101, // 0x0265
    0b00000001_10110010  // 0x01B2
};

// data_byte: 8 bits (as unsigned char)
// parity_matrix: 8 rows, each 8 bits (unsigned char[8])
// Returns: 16-bit codeword (8 parity bits | 8 data bits)
unsigned short encode(uint8_t data_byte) {
    unsigned short codeword = 0;
    // Compute parity bits (high 8 bits)
    for (int i = 0; i < 8; ++i) {
        uint8_t parity = 0;
        for (int j = 0; j < 8; ++j) {
            // Get j-th bit of data_byte
            uint8_t data_bit = (data_byte >> (7 - j)) & 1;
            uint8_t matrix_bit = (parity_matrix[i] >> (7 - j)) & 1;
            parity ^= (data_bit & matrix_bit);
        }
        codeword |= (parity << (15 - i));
    }
    // Copy data bits (low 8 bits)
    codeword |= (data_byte & 0xFF);
    return codeword;
}

// H: const unsigned short H[8]
// LUT: const unsigned short LUT[256]
// codeword: 16 bits (unsigned short)
// Returns: corrected data byte (unsigned char)
unsigned char decode(unsigned short codeword) {
    // Compute syndrome (8 bits)
    uint8_t syndrome = 0;
    for (int i = 0; i < 8; ++i) {
        // Dot product of H[i] and codeword, mod 2
        unsigned short row = H[i];
        unsigned short x = codeword & row;
        // Count number of 1s in x
        int parity = 0;
        while (x) {
            parity ^= (x & 1);
            x >>= 1;
        }
        syndrome = (syndrome << 1) | (parity & 1);
    }

    // Look up error pattern in LUT
    unsigned short error_pattern = LUT[syndrome];

    // Correct the codeword
    unsigned short corrected = codeword ^ error_pattern;

    // Return the lower 8 bits (data byte)
    return (unsigned char)(corrected & 0xFF);
}

int main() {
    // Example usage
    for (uint8_t data_byte = 0b10101010; data_byte < 256; data_byte++) {
        unsigned short encoded = encode(data_byte);
        printf("Data byte: 0x%02X, Encoded: 0x%04X\n", data_byte, encoded);
        unsigned char decoded = decode(encoded);
        printf("Decoded: 0x%02X\n", decoded);

        if (decoded == data_byte) {
            printf("Decoding successful!\n");
        } else {
            printf("Decoding failed!\n");
        }
    }


    return 0;
}