from keras.models import *
from keras.layers import *
from keras.optimizers import *

class PawnNet():
    def __init__(self, action_size, args, board_x=9, board_y =9, num_channels_feature = 19*5):
        # game params
        self.board_x, self.board_y = board_x, board_y
        self.action_size = action_size
        self.args = args

        # Neural Net
        self.input_boards = Input(shape=(self.board_x, self.board_y,num_channels_feature))    # s: batch_size x board_x x board_y

        h_conv1 = Activation('elu')(BatchNormalization(axis=3)(Conv2D(args['num_channels'], 3, padding='same', use_bias=False)(self.input_boards)))         # batch_size  x board_x x board_y x num_channels
        h_conv2 = Activation('elu')(BatchNormalization(axis=3)(Conv2D(args['num_channels'], 3, padding='same', use_bias=False)(h_conv1)))         # batch_size  x board_x x board_y x num_channels
        h_conv3 = Activation('elu')(BatchNormalization(axis=3)(Conv2D(args['num_channels'], 3, padding='valid', use_bias=False)(h_conv2)))        # batch_size  x (board_x-2) x (board_y-2) x num_channels
        h_conv4 = Activation('elu')(BatchNormalization(axis=3)(Conv2D(args['num_channels'], 3, padding='valid', use_bias=False)(h_conv3)))        # batch_size  x (board_x-4) x (board_y-4) x num_channels
        h_conv4_flat = Flatten()(h_conv4)
        s_fc1 = Dropout(args['dropout'])(Activation('elu')(BatchNormalization(axis=1)(Dense(1024, use_bias=False)(h_conv4_flat))))  # batch_size x 1024
        s_fc2 = Dropout(args['dropout'])(Activation('elu')(BatchNormalization(axis=1)(Dense(512, use_bias=False)(s_fc1))))          # batch_size x 1024
        self.pi = Dense(self.action_size, activation='softmax', name='pi')(s_fc2)   # batch_size x self.action_size
        self.v = Dense(1, activation='tanh', name='v')(s_fc2)                    # batch_size x 1

        self.model = Model(inputs=self.input_boards, outputs=[self.pi, self.v])
        self.model.compile(loss=['categorical_crossentropy','mean_squared_error'], optimizer=Adam(args['lr']))

class PawnNetZero():
    def __init__(self,action_size, board_x=9, board_y =9, num_channels_feature = 28*5):
        self.board_x, self.board_y = board_x, board_y
        self.action_size = action_size

        self.input_boards = Input(shape=(self.board_x, self.board_y,num_channels_feature))    # s: batch_size x board_x x board_y
        x = Conv2D(filters=199, kernel_size=(4,4), padding='same', activation='linear')(self.input_boards)

        x = BatchNormalization(axis=3)(x)
        x = LeakyReLU()(x)
        for _ in range(4):
            x = self.residual_layer(x, 199, (4,4))
        self.value_head = self.value_head(x)
        self.policy_head = self.policy_head(x)

        self.model = Model(inputs=[self.input_boards], outputs=[self.policy_head,self.value_head])
        self.model.compile(loss=['categorical_crossentropy','mean_squared_error'], optimizer=Adam(0.001))

    def conv_layer(self, x, filters, kernel_size):
        x = Conv2D(
            filters=filters
            , kernel_size=kernel_size
            , padding='same'
            , activation='linear'
        )(x)

        x = BatchNormalization(axis=3)(x)
        x = LeakyReLU()(x)

        return (x)

    def residual_layer(self, input_block, filters, kernel_size):
        x = self.conv_layer(input_block, filters, kernel_size)

        x = Conv2D(
            filters=filters
            , kernel_size=kernel_size
            , padding='same'
            , activation='linear'
        )(x)

        x = BatchNormalization(axis=3)(x)

        x = add([input_block, x])

        x = LeakyReLU()(x)

        return (x)

    def value_head(self, x):
        x = Conv2D(
            filters=1
            , kernel_size=(1, 1)
            , padding='same'
            , activation='linear'
        )(x)

        x = BatchNormalization(axis=3)(x)
        x = LeakyReLU()(x)

        x = Flatten()(x)

        x = Dense(
            180
            , activation='linear'
        )(x)

        x = LeakyReLU()(x)

        x = Dense(
            1
            , activation='tanh'
            , name='value_head'
        )(x)

        return (x)

    def policy_head(self, x):

        x = Conv2D(
        filters = 2
        , kernel_size = (1,1)
        , padding = 'same'
        , activation='linear'
        )(x)

        x = BatchNormalization()(x)
        x = LeakyReLU()(x)

        x = Flatten()(x)

        x = Dense(
            self.action_size
            , activation='softmax'
            , name = 'policy_head'
            )(x)

        return (x)