# ======================================================= IMPORTS ======================================================= #
import tensorflow as tf
import os
import numpy as np
import copy

os.environ['TF_CPP_MIN_LOG_LEVEL']='2' # Removing warnings

# ==================================================== NN CHECK ==================================================== #

def check_nn_config(layers,conv_layers,fc_layers,conv_z_matrix,fil_size_matrix,
                    pooling_matrix,stride_matrix,pool_stride_matrix,pool_type,
                    activation_type,input_x,input_y,input_z):

    nn_config_valid = 1

    if ( (conv_layers + fc_layers) > layers ) or ( (conv_layers + fc_layers) < layers ):
        print('Error: Invalid values for conv_layers and fc layers')
        nn_config_valid = 0
    elif ( len(conv_z_matrix) > conv_layers ) or ( len(conv_z_matrix) < conv_layers ):
        print('Error: Invalid values for conv_z_matrix')
    elif ( len(fil_size_matrix) > conv_layers ) or ( len(fil_size_matrix) < conv_layers ):
        print('Error: Invalid values for fil_size_matrix')
        nn_config_valid = 0
    elif (len(pooling_matrix) < conv_layers) or (len(pooling_matrix) > conv_layers):
        print('Error: Invalid values for pool_matrix')
        nn_config_valid = 0
    elif (len(stride_matrix) < conv_layers) or (len(stride_matrix) > conv_layers):
        print('Error: Invalid values for stride_matrix')
        nn_config_valid = 0
    elif (len(pool_stride_matrix) < conv_layers) or (len(pool_stride_matrix) > conv_layers):
        print('Error: Invalid values for pool_stride_matrix')
        nn_config_valid = 0
    else:
        for layer in range(0,conv_layers):

            print('\n-------- Layer {} Check Dimensions --------'.format(layer))

            if layer == 0:
                current_parameters = [1,input_x,input_y,input_z]
                channel_input = input_z
            else:
                channel_input = conv_z_matrix[layer-1]

            weights = [ fil_size_matrix[layer],fil_size_matrix[layer],channel_input,conv_z_matrix[layer] ]
            bias = [conv_z_matrix[layer]]

            convolution_x = int( np.floor( (current_parameters[1]-weights[0])/stride_matrix[layer][0] ) + 1 )
            convolution_y = int( np.floor( (current_parameters[2]-weights[1])/stride_matrix[layer][1] ) + 1 )
            conv = [1,convolution_x,convolution_y,conv_z_matrix[layer]]

            pool_x = int( np.floor( (conv[1]-pooling_matrix[layer][0])/pool_stride_matrix[layer][0] ) + 1 )
            pool_y = int( np.floor( (conv[2]-pooling_matrix[layer][1])/pool_stride_matrix[layer][1] ) + 1 )
            pool = [1,pool_x,pool_y,conv_z_matrix[layer]]

            print("Weights: {}".format(weights))
            print("Bias: {}".format(bias))
            print("Conv: {}".format(conv))
            print("Pool: {}".format(pool))

            for weight_parameter in weights:
                if weight_parameter <= 0:
                    print("Error: invalid network layer {}, weights must be > 0".format(layer))
                    return 0

            for bias_parameter in bias:
                if bias_parameter <= 0:
                        print("Error: invalid network layer {}, bias must be > 0".format(layer))
                        return 0

            for conv_parameter in conv:
                if conv_parameter <= 0:
                    print("Error: invalid network layer {}, conv must be > 0".format(layer))
                    return 0

            for pool_parameter in pool:
                if pool_parameter <= 0:
                    print("Error: invalid network layer {}, pool must be > 0".format(layer))
                    return 0

            current_parameters = pool

    return nn_config_valid

# ==================================================== OUTPUT SHAPE FCTN ==================================================== #

def get_output_shape(layers,conv_layers,fc_layers,conv_z_matrix,fil_size_matrix,
                    pooling_matrix,stride_matrix,pool_stride_matrix,pool_type,
                    activation_type,input_x,input_y,input_z):
    
    for layer in range(0, conv_layers):

        if layer == 0:
            current_parameters = [None, input_x, input_y, input_z]
            channel_input = input_z
        else:
            channel_input = conv_z_matrix[layer - 1]

        weights = [fil_size_matrix[layer], fil_size_matrix[layer], channel_input, conv_z_matrix[layer]]
        bias = [conv_z_matrix[layer]]

        convolution_x = int(np.floor((current_parameters[1] - weights[0]) / stride_matrix[layer][0]) + 1)
        convolution_y = int(np.floor((current_parameters[2] - weights[1]) / stride_matrix[layer][1]) + 1)
        conv = [None, convolution_x, convolution_y, conv_z_matrix[layer]]

        pool_x = int(np.floor((conv[1] - pooling_matrix[layer][0]) / pool_stride_matrix[layer][0]) + 1)
        pool_y = int(np.floor((conv[2] - pooling_matrix[layer][1]) / pool_stride_matrix[layer][1]) + 1)
        pool = [None, pool_x, pool_y, conv_z_matrix[layer]]

        current_parameters = pool

    return pool

# ==================================================== NN CLASS ==================================================== #

class conv_net():

    def __init__(self,layers,conv_layers,fc_layers,conv_z_matrix,fil_size_matrix,
               pooling_matrix,stride_matrix,pool_stride_matrix,pool_type,activation_type,
               input_x,input_y,input_z,output_shape): # Constructor
        
        #Total number of layers
        self.num_layers = layers
        
        
        self.num_conv_layers = conv_layers
        self.num_fc_layers = fc_layers
        self.conv_z_sizes = conv_z_matrix
        self.fil_sizes = fil_size_matrix
        self.pool_sizes = pooling_matrix
        self.stride_sizes = stride_matrix
        self.pool_stride_sizes = pool_stride_matrix
        self.pool_type = pool_type
        self.activation_type = activation_type
        
        tf.reset_default_graph()
        
        self.input_pixels = tf.placeholder(tf.float32,shape=(None, input_x,input_y,input_z),name='input_pixels') # This is the input that will be fed externally
        self.input_data = tf.reshape(self.input_pixels,[-1,input_x,input_y,input_z]) # Reshaping the input
        
        # Placeholder for learning rate
        self.gradient_val = tf.placeholder(tf.float32, shape=())

        self.current_layer_shape = []
        self.current_parameters = []
        self.current_weights = []
        self.current_bias = []
        self.current_convolution = []
        self.current_activation = []
        self.current_pool = []
        self.num_iterations = tf.Variable(0,dtype=tf.float32)
        # self.cost_function_in = tf.placeholder(tf.float32,shape=[])#tf.Variable(0,dtype=tf.float32)
        
        # inits layers in a loop
        
        
        '''for layer in range(0,self.num_conv_layers):

            if layer == 0:
                channel_input = input_z
                self.current_parameters.append(self.input_data)
            else:
                channel_input = self.conv_z_sizes[layer-1]

            self.current_weights.append( init_weight_var([self.fil_sizes[layer],self.fil_sizes[layer],channel_input,self.conv_z_sizes[layer]]) )
            self.current_bias.append( init_bias_var([self.conv_z_sizes[layer]]) )
            self.current_convolution.append( convolution(self.current_parameters[layer],self.current_weights[layer],self.stride_sizes[layer]) + self.current_bias[layer] )
            self.current_activation.append( activation(self.current_convolution[layer],activation_type=self.activation_type) )
            self.current_pool.append( pool(self.current_activation[layer],self.pool_sizes[layer],self.pool_stride_sizes[layer],pool_type=self.pool_type) )
            self.current_parameters.append( self.current_pool[layer] )

            print('\n-------- Layer {} Param Dimensions --------'.format(layer))
            
            # input to current layer
            print("CP: {}".format(self.current_parameters[layer]))
            
            # weights and bias for this layerf
            print("CW: {}".format(self.current_weights[layer]))
            print("CB: {}".format(self.current_bias[layer]))
            
            # matrix after convolution
            print("CC: {}".format(self.current_convolution[layer]))
            
            # Activation layer
            print("CA: {}".format(self.current_activation[layer]))
            
            # Pool layer
            print("CPl: {}".format(self.current_pool[layer]))'''
        

        self.ACTUAL_OUTPUT = tf.placeholder(tf.float32, shape=(None,1), name='ACTUAL_OUTPUT')
        #self.NN_OUTPUT = tf.sigmoid(tf.reshape(self.current_parameters[self.num_conv_layers],shape=[-1,1])
        self.NN_OUTPUT = createConvNet(self.input_data, 10, 1, 0.25, reuse=False,
                            is_training=True)
        self.AC_OUTPUT = tf.reshape(self.ACTUAL_OUTPUT,shape=[-1,1])
        self.AC_c = tf.reshape(self.AC_OUTPUT,shape=[-1,1])
        #self.AC_pos_h, self.AC_pos_w, self.AC_pos_x, self.AC_pos_y, self.AC_p, self.AC_c = tf.split(self.AC_OUTPUT, 6, 0)
        #self.NN_pos_h, self.NN_pos_w, self.NN_pos_x, self.NN_pos_y, self.NN_p, self.NN_c_unformatted = tf.split(self.NN_OUTPUT, 6, 0)

        #self.AC_c = tf.round(self.AC_c
        #zero_const = tf.constant(0, shape=[], dtype=tf.float32)
        #one_const = tf.constant(1, shape=[], dtype=tf.float32)
        #cond_const = tf.constant(0.5,shape=[], dtype=tf.float32)
        #self.NOT_AC_c = tf.round(tf.cast(tf.equal(self.AC_c, zero_const), dtype=tf.float32))
        #self.NN_c = tf.reshape(self.NN_c_unformatted,shape=[])
        self.NN_c = tf.reshape(self.NN_OUTPUT,shape=[-1,1])

        # def set_zero(): return zero_const#tf.multiply(self.NN_c,zero_const)
        # def set_one(): return one_const #tf.floor(tf.add(self.NN_c,one_const))
        # self.NN_c_unformatted = self.NN_c
        # self.NN_c = tf.cond(tf.less(self.NN_c,cond_const),set_zero,set_one)

        # ==================================== LOSS FUNCTION ==================================== #

        # alpha_coord = tf.constant(5, sha pe=[], dtype=tf.float32)
        # alpha_no_obj = tf.constant(0.5, shape=[], dtype=tf.float32)
        # alpha_class = tf.constant(1, shape=[], dtype=tf.float32)

        # self.pos_err_c = tf.multiply(alpha_coord,tf.multiply(self.AC_p ,tf.abs(tf.add(tf.square(tf.subtract(self.NN_pos_x,self.AC_pos_x)) ,tf.square(tf.subtract(self.NN_pos_y,self.AC_pos_y))))))
        # self.size_err_c = tf.multiply(alpha_coord,tf.multiply( self.AC_p ,tf.abs(tf.add(tf.square(tf.subtract(self.NN_pos_w,self.AC_pos_w)) , tf.square(tf.subtract(self.NN_pos_h,self.AC_pos_h)) ))))
        # self.class_err_c = tf.multiply(alpha_class,tf.add( tf.multiply( self.AC_p, tf.square(tf.subtract(self.NN_c,self.AC_c)) ) , tf.multiply(alpha_no_obj , tf.multiply( self.AC_p, tf.square(tf.subtract(self.NN_c,self.AC_c)) ))))
        # self.prob_err_c = tf.multiply(self.AC_p,tf.abs(tf.subtract(self.AC_p,self.NN_p)))

        #alpha_pos = tf.constant(1, shape=[], dtype=tf.float32)
        #pos_err_a = tf.abs(tf.add( tf.square(tf.subtract(self.NN_pos_x,self.AC_pos_x)) , tf.square(tf.subtract(self.NN_pos_y,self.AC_pos_y)) ))
        #pos_err_b = tf.multiply(self.AC_c,pos_err_a)
        #self.pos_err_c = tf.multiply(alpha_pos,pos_err_b)

        #alpha_size = tf.constant(1, shape=[], dtype=tf.float32)
        #size_err_a = tf.abs(tf.add(tf.square(tf.subtract(self.NN_pos_w, self.AC_pos_w)), tf.square(tf.subtract(self.NN_pos_h, self.AC_pos_h))))
        #size_err_b = tf.multiply(self.AC_c, size_err_a)
        #self.size_err_c = tf.multiply(alpha_size, size_err_b)

        '''alpha_class = tf.constant(50, shape=[], dtype=tf.float32)
        alpha_no_obj = tf.constant(50, shape=[], dtype=tf.float32)
        class_err_a1 = tf.square(tf.subtract(self.NN_c, self.AC_c))
        self.class_err_b1 = tf.multiply(alpha_class,tf.multiply(self.AC_c,class_err_a1))
        self.class_err_b2 = tf.multiply(alpha_no_obj,tf.multiply(self.NOT_AC_c,class_err_a1))
        self.class_err_c = tf.add(self.class_err_b1,self.class_err_b2)'''

        #alpha_prob = tf.constant(1, shape=[], dtype=tf.float32)
        #prob_err_a = tf.square(tf.subtract(self.NN_p, self.AC_p))
        #self.prob_err_c = tf.multiply(alpha_prob,tf.multiply(self.AC_p, prob_err_a))

        #self.var_gradient = tf.gradients(self.class_err_c,self.NN_c)
        # ======================================================================================= #
         
        
        #one = tf.constant(1, dtype = tf.float32)
        #AccVar = tf.Variable(self.AC_c, dtype=tf.float32)
        #NNcVar = tf.Variable(self.NN_c, dtype=tf.float32)
        
        #partA = tf.multiply(AccVar, tf.log(NNcVar))
        #partB = tf.multiply(tf.subtract(one, AccVar), tf.log(tf.subtract(one, NNcVar)))
        
        #self.cost_function_out = tf.add(partA, partB)  
        
        #self.cost_function_out = tf.reduce_mean(tf.squared_difference(self.AC_c, self.NN_c))
        self.cost_function_out = -tf.reduce_mean(self.AC_c*tf.log(self.NN_c+1e-10) + (1-self.AC_c)*tf.log(1-(self.NN_c+1e-10)))
        self.train_step = tf.train.AdamOptimizer(self.gradient_val).minimize(self.cost_function_out)
        self.output_correct = tf.equal(self.AC_c,self.NN_c)

        self.sess = tf.InteractiveSession()
        self.sess.run(tf.global_variables_initializer())
    
    '''
        Executes one step of cost optimization
        
        Inputs:
        pixels: the input pixel data
        actual_output: label for the pixel data
        gradient_val: gradients from previous execution
        cost_func_acm: previous cost 
        
        Outputs:
        
        
    '''
    #def execute(self, pixels, actual_output, gradient_val, cost_func_acm):
    def execute(self, inpBatch, grad_val):
        
        # executes the network
        #A_c, NN_c, CF, BPE, BSE, BCE, BPRE, OC, A_pos_x, A_pos_y, NN_pos_x, NN_pox_y, G, NN_c_unformatted, var_grad = self.sess.run\
        #objList1 = [self.AC_c, self.NN_c, self.cost_function_out, self.error, self.output_correct,self.gradients, self.current_weights[6]]
        #print('objList1')
        '''for i in range(len(objList1)):
        print('object: ', objList1[i], ' : ', objList1[i] is None)'''
        
        print('Number of data feeded into net: ', len(inpBatch[0]))
        #print('Grad value: ', type(grad_val))
        #l =  [self.AC_c, self.NN_c, self.output_correct, self.gradients, self.cost_function_out]
        '''for i in l:
            print(tf.shape(l))'''
        
        # fdict= [inpBatch[0], inpBatch[1]]
        inpB = copy.deepcopy(inpBatch)
        xs = np.array(inpB[0]).astype(np.float32)
        ys = (np.array(inpB[1]).astype(np.float32)).reshape((-1,1))
        
        print('xs: ', np.shape(xs))
        print('ys: ',np.shape(ys))
        
        #print(xs)
        #print(ys)
        # for i in fdict:
        
        # print('objList2')
        #objList2 = [pixels, actual_output, gradient_val, cost_func_acm]
        '''for i in range(len(objList2)):
            print('object : ', objList2[i] is None)
        '''
        
        # current_weights[6] has none values
        # Runs one step of optimization
        A_c, NN_c, OC, CF= self.sess.run \
        (
            [self.AC_c, self.NN_c, self.output_correct, self.cost_function_out],
            feed_dict={self.input_pixels:xs, self.ACTUAL_OUTPUT:ys, self.gradient_val:np.array(grad_val).astype(np.float32)}

            # [self.AC_c, self.NN_c, self.cost_function, self.pos_err_c, self.size_err_c, self.class_err_c, self.prob_err_c, self.output_correct,
            #  self.AC_pos_x, self.AC_pos_y, self.NN_pos_x, self.NN_pos_y, self.gradients,self.NN_c_unformatted,self.gradients],
            # feed_dict={self.input_pixels: pixels, self.AC_OUTPUT: actual_output, self.gradient_val: gradient_val}
        )
        
        print('Correct Answer: ', A_c)
        print('Predictions: ', NN_c)
        
        # CW =  self.current_weights[6]
        return A_c, NN_c, OC, CF
        #return A_c, NN_c, BPE, BSE, BCE, BPRE, CF, OC, A_pos_x, A_pos_y, NN_pos_x, NN_pox_y, G, NN_c_unformatted, var_grad
        

# ==================================================== NN OPERATIONS ==================================================== #

def init_weight_var(shape):

    weight_var = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(weight_var, dtype=tf.float32)

def init_bias_var(shape):

    bias_var = tf.constant(0.1, shape=shape)
    return tf.Variable(bias_var, dtype=tf.float32)

def convolution(parameters,weights,stride_size,padding_type='VALID'):

    convolution = tf.nn.conv2d(parameters, weights, strides=[1,stride_size[0],stride_size[1],1], padding=padding_type)
    return convolution

def pool(parameters,pool_size,pool_stride_size=[1,1,1,1],padding_type='VALID',pool_type='MAX'):

    # TO DO: Figure out how pool_stride_size will affect this equation and integrate

    if pool_type == 'MAX':
        pool = tf.nn.max_pool(parameters, ksize=[1,pool_size[0],pool_size[1],1], strides=[1,pool_stride_size[0],pool_stride_size[1],1], padding=padding_type)
    elif pool_type == 'AVG':
        pool = tf.nn.avg_pool(parameters, ksize=[1,pool_size[0],pool_size[1],1], strides=[1,pool_stride_size[0],pool_stride_size[1],1], padding=padding_type)

    return pool

def activation(parameters,activation_type = 'RELU'):

    if activation_type == 'RELU':
        activation = tf.nn.relu(parameters)
    elif activation_type == 'SIG':
        activation = tf.nn.sigmoid(parameters)

    return activation

'''
Source: https://github.com/aymericdamien/TensorFlow-Examples/tree/master/examples/3_NeuralNetworks

'''
def createConvNet(xData, n_convlayers, n_classes, dropout, reuse, is_training):
    # Define a scope for reusing the variables
    

    with tf.variable_scope('ConvNet', reuse=reuse):

        # MNIST data input is a 1-D vector of 784 features (28*28 pixels)
        # Reshape to match picture format [Height x Width x Channel]
        # Tensor input become 4-D: [Batch Size, Height, Width, Channel]
        x = tf.reshape(xData, shape=[-1, 128, 128, 3])
        # Convolution Layer with 20 filters and a kernel size of 5
        conv1 = tf.layers.conv2d(x, 20, 5, activation=tf.nn.relu)
        
        # Max Pooling (down-sampling) with strides of 2 and kernel size of 2
        conv1 = tf.layers.max_pooling2d(conv1, 2, 2)

        # Convolution Layer with 10 filters and a kernel size of 3
        conv2 = tf.layers.conv2d(conv1, 10, 5, activation=tf.nn.relu)
        
        # Max Pooling (down-sampling) with strides of 2 and kernel size of 2
        conv2 = tf.layers.max_pooling2d(conv2, 2, 2)
        
        conv3 = tf.layers.conv2d(conv2, 5, 5, activation=tf.nn.relu)
        conv3 = tf.layers.max_pooling2d(conv3, 2, 2)
        # Flatten the data to a 1-D vector for the fully connected layer
        fc1 = tf.contrib.layers.flatten(conv3)
            
        # Fully connected layer (in tf contrib folder for now)
        fc1 = tf.layers.dense(fc1, 100)
        # Apply Dropout (if is_training is False, dropout is not applied)
        fc1 = tf.layers.dropout(fc1, rate=dropout, training=is_training)

        # Output layer, class prediction
        out = tf.sigmoid(tf.layers.dense(fc1, n_classes))

    return out


