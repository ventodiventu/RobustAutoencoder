import tensorflow as tf
import numpy as np

class Sparsel21_Deep_Autoencoder():
    def __init__(self, sess, input_dim_list=[784,400], sparsities = [0.5]):
        """input_dim_list must include the original data dimension"""
        assert len(input_dim_list) >= 2
        assert len(sparsities) == len(input_dim_list) - 1
        self.W_list = []
        self.encoding_b_list = []
        self.decoding_b_list = []
        self.dim_list = input_dim_list
        self.sparsities = sparsities
        self.penal_term = []
        ## Encoders parameters
        for i in range(len(input_dim_list)-1):

            self.W_list.append(tf.Variable(tf.random_uniform([self.dim_list[i],self.dim_list[i+1]],-1.0,1.0)))

            self.encoding_b_list.append(tf.Variable(tf.random_uniform([self.dim_list[i+1]],-1.0,1.0)))
        ## Decoders parameters
        for i in range(len(input_dim_list)-2,-1,-1):
            self.decoding_b_list.append(tf.Variable(tf.random_uniform([self.dim_list[i]],-1.0,1.0)))

        self.input_x = tf.placeholder(tf.float32,[None,self.dim_list[0]])

        ## coding graph :
        last_layer = self.input_x
        for weight,bias in zip(self.W_list,self.encoding_b_list):
            hidden = tf.sigmoid(tf.matmul(last_layer,weight) + bias)
            self.penal_term.append(tf.norm(tf.norm(hidden,ord=2,axis=0),ord=1))
            last_layer = hidden
        ## decode graph:
        for weight,bias in zip(reversed(self.W_list),self.decoding_b_list):
            hidden = tf.sigmoid(tf.matmul(last_layer,tf.transpose(weight)) + bias)
            last_layer = hidden
        recon = last_layer

        #cost = tf.reduce_mean(tf.square(input_x - recon))
        cost = 200 * tf.losses.log_loss(recon, self.input_x)
        for penalty_term, sparcity in zip(self.penal_term,self.sparsities):
            cost += sparcity * penalty_term
        self.cost =cost

        sess.run(tf.global_variables_initializer())

    def fit(self, X, sess, learning_rate=0.15,
            iteration=200, batch_size=50, verbose=False):
        assert X.shape[1] == self.dim_list[0]


        opt = tf.train.GradientDescentOptimizer(learning_rate)
        train_step = opt.minimize(self.cost)

        error = []
        sample_size = X.shape[0]

        def batches(l, n):
            """Yield successive n-sized chunks from l."""
            for i in xrange(0, l, n):
                yield range(i,min(l,i+n))

        for i in xrange(iteration):
            for one_batch in batches(sample_size, batch_size):
                sess.run(train_step,feed_dict = {self.input_x:X[one_batch]})

            if verbose:
                e = self.cost.eval(session = sess,feed_dict = {self.input_x: X[one_batch]})
                error.append(e)
                if i%20==0:
                    print "    iteration : ", i ,", cost : ", e

        return error
    def transform(self, X, sess):
        new_input = tf.placeholder(tf.float32,[None,self.dim_list[0]])
        last_layer = new_input
        for weight,bias in zip(self.W_list,self.encoding_b_list):
            hidden = tf.sigmoid(tf.matmul(last_layer,weight) + bias)
            last_layer = hidden
        return hidden.eval(session = sess, feed_dict={new_input: X})

    def getRecon(self, X, sess):
        hidden_data = self.transform(X, sess)
        hidden_layer = tf.placeholder(tf.float32,[None,self.dim_list[-1]])
        last_layer = hidden_layer
        for weight,bias in zip(reversed(self.W_list),self.decoding_b_list):
            hidden = tf.sigmoid(tf.matmul(last_layer,tf.transpose(weight)) + bias)
            last_layer = hidden
        recon = last_layer
        return recon.eval(session = sess,feed_dict={hidden_layer:hidden_data})
if __name__ == '__main__':
    x = np.load(r"/home/zc/Documents/train_x_small.pkl")

    with tf.Session() as sess:

        sae = Sparsel21_Deep_Autoencoder(sess = sess, input_dim_list=[784,784,784],sparsities=[0.5,0.5])
        print "x type",x.shape,x.dtype
        error = sae.fit(x, sess = sess, iteration = 21,batch_size=97,verbose = True)
        print error
        h = sae.transform(x,sess=sess)
        print "h shape",h.shape
        R = sae.getRecon(x,sess=sess)
        print "R",R.shape,R.dtype
        error = sae.fit(R, sess = sess, iteration = 21,batch_size=97,verbose = True)
        print error
