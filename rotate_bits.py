def rotate_bits(num, rot):
	return (num << rot) & 0xFFFFFFFF

num = int(input("Enter a number: "))
rot = int(input("Enter the number of positions to rotate: "))

result = rotate_bits(num, rot)
print("The result of the rotation is:", result)
