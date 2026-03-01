# EE24B092
def matrix_multiply(matrix1, matrix2):
    # This function should be implemented by the students
    m1=len(matrix1) # rows in mat1
    m2=len(matrix2) # rows in mat 2
    
    if (m1==0 and m2==0):
        return [] # return empty if both matrices are empty
    if (m1==0 or m2==0): 
        raise ValueError("incompatible matrices") # if one of them is empty, raise error
        return
    
    n1=len(matrix1[0]) # columns in mat1
    n2=len(matrix2[0]) # columns in mat2
    
    if (n1!=m2): 
        raise ValueError("incompatible matrices") #if cols in mat1 != rows in mat2
        return
	
    ans_matrix=[] # initialise an empty list
    
    for row in range(m1):
        ans_matrix.append([]) # appends a new row in answer matrix
        for column in range(n2):
            x=0 # to initialise the element ans_matrix[row][column]
            for idx in range(n1):
                x+=matrix1[row][idx]*matrix2[idx][column] # matrix multiplication math => sum over 0<=i<n1 mat1[row][i]*mat2[i][column]
            ans_matrix[row].append(x) # append to the current row
                    
    return ans_matrix
		



