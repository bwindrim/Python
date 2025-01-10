import numpy as np
from itertools import combinations

# Function to generate LUT (from the previous example)
def generate_lut(parity_matrix):
    n = 16 #parity_matrix.shape[1]  # Total number of bits (16)
    k = 8 #n - parity_matrix.shape[0]  # Number of data bits (8)
    print(f'n = {n}, k = {k}')

    # Construct H matrix (transpose of parity matrix with identity block)
    identity_block = np.eye(8, dtype=int)
    H = np.hstack((identity_block, parity_matrix.T))
    
    # Debugging: Print shapes of H and error_vector
    print(parity_matrix)
    print("Shape of H:", H.shape)
    print(H)

    # Initialize LUT dictionary
    lut = {}
    
    # Add single-bit error syndromes
    for i in range(n):
        error_vector = np.zeros(n, dtype=int)
        #print("Shape of error_vector:", error_vector.shape)
        error_vector[i] = 1
        syndrome = np.dot(H, error_vector) % 2
        lut[tuple(syndrome)] = error_vector
    
    # Add two-bit error syndromes
    for i, j in combinations(range(n), 2):
        error_vector = np.zeros(n, dtype=int)
        error_vector[i] = 1
        error_vector[j] = 1
        syndrome = np.dot(H, error_vector) % 2
        lut[tuple(syndrome)] = error_vector
    
    return lut, H

# Function to print LUT as a C array
def print_lut_as_c_array(lut):
    print("unsigned char lut[][16] = {")
    for syndrome, error_vector in lut.items():
        syndrome_str = ", ".join(map(str, syndrome))
        error_vector_str = ", ".join(map(str, error_vector))
        print(f"    {{{syndrome_str}}}, {{{error_vector_str}}},")
    print("};")

# Parity matrix (P) from the paper
P = np.array([
    [0, 1, 0, 0, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 1, 1, 0],
    [0, 1, 0, 1, 0, 0, 1, 1],
    [1, 0, 1, 0, 1, 0, 0, 1],
    [1, 1, 0, 1, 0, 1, 0, 0],
    [0, 1, 1, 0, 1, 0, 1, 0],
    [0, 0, 1, 1, 0, 1, 0, 1],
    [1, 0, 0, 1, 1, 0, 1, 0]
])

# Generate LUT and H matrix
lut, H = generate_lut(P)

# Print LUT as a C array
print_lut_as_c_array(lut)

# Function to encode data
def encode(data_byte, parity_matrix):
    parity = np.dot(data_byte, parity_matrix) % 2
    return np.hstack((parity, data_byte))

# Function to decode data using LUT
def decode(encoded_word, H, lut):
    syndrome = np.dot(H, encoded_word) % 2
    error_vector = lut.get(tuple(syndrome), None)
    if error_vector is not None:
        corrected_word = (encoded_word + error_vector) % 2
        return corrected_word[-8:]  # Extract original data byte
    else:
        return None  # Uncorrectable error

# Test all possible 8-bit data words
all_data_words = [np.array(list(np.binary_repr(i, width=8)), dtype=int) for i in range(256)]

# Counters
total_tests = 0
successful_corrections = 0

for data_byte in all_data_words:
    # Encode the data
    encoded_word = encode(data_byte, P)
    
    # Test 1-bit errors
    for i in range(16):
        error_vector = np.zeros(16, dtype=int)
        error_vector[i] = 1
        corrupted_word = (encoded_word + error_vector) % 2
        corrected_data = decode(corrupted_word, H, lut)
        total_tests += 1
        if np.array_equal(corrected_data, data_byte):
            successful_corrections += 1
    
    # Test 2-bit errors
    for i, j in combinations(range(16), 2):
        error_vector = np.zeros(16, dtype=int)
        error_vector[i] = 1
        error_vector[j] = 1
        corrupted_word = (encoded_word + error_vector) % 2
        corrected_data = decode(corrupted_word, H, lut)
        total_tests += 1
        if np.array_equal(corrected_data, data_byte):
            successful_corrections += 1

# Report results
print(f"Total tests: {total_tests}")
print(f"Successful corrections: {successful_corrections}")
print(f"Success rate: {successful_corrections / total_tests * 100:.2f}%")