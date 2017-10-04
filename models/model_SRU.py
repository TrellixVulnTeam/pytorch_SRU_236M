import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import numpy as np
import random
import torch.nn.init as init
from models import cuda_functional as MF
import hyperparams
torch.manual_seed(hyperparams.seed_num)
random.seed(hyperparams.seed_num)


class SRU(nn.Module):
    def __init__(self, args):
        super(SRU, self).__init__()
        self.args = args
        self.hidden_dim = args.lstm_hidden_dim
        self.num_layers = args.lstm_num_layers
        V = args.embed_num
        D = args.embed_dim
        C = args.class_num
        self.dropout = nn.Dropout(args.dropout)
        self.dropout_embed = nn.Dropout(args.dropout_embed)
        self.embed = nn.Embedding(V, D)
        if args.word_Embedding:
            pretrained_weight = np.array(args.pretrained_weight)
            self.embed.weight.data.copy_(torch.from_numpy(pretrained_weight))

        self.sru = MF.SRU(input_size=D, hidden_size=self.hidden_dim, num_layers=self.num_layers,
                          dropout=self.args.dropout, bidirectional=False)
        print(self.sru)
        # if args.init_weight:
        #     print("Initing W .......")
        #     init.xavier_normal(self.bilstm.all_weights[0][0], gain=np.sqrt(args.init_weight_value))
        #     init.xavier_normal(self.bilstm.all_weights[0][1], gain=np.sqrt(args.init_weight_value))
        #     init.xavier_normal(self.bilstm.all_weights[1][0], gain=np.sqrt(args.init_weight_value))
        #     init.xavier_normal(self.bilstm.all_weights[1][1], gain=np.sqrt(args.init_weight_value))
        self.hidden2label = nn.Linear(self.hidden_dim, C)
        self.hidden = self.init_hidden(self.num_layers, args.batch_size)
        print("self.hidden", self.hidden)

    def init_hidden(self, num_layers, batch_size):
        # the first is the hidden h
        # the second is the cell  c
        return (Variable(torch.zeros(2 * num_layers, batch_size, self.hidden_dim)),
                Variable(torch.zeros(2 * num_layers, batch_size, self.hidden_dim)))

    def forward(self, x):
        x = self.embed(x)
        x = self.dropout_embed(x)
        # x = x.view(len(x), x.size(1), -1)
        # x = embed.view(len(x), embed.size(1), -1)
        bilstm_out, self.hidden = self.sru(x)

        bilstm_out = torch.transpose(bilstm_out, 0, 1)
        bilstm_out = torch.transpose(bilstm_out, 1, 2)
        bilstm_out = F.tanh(bilstm_out)
        bilstm_out = F.max_pool1d(bilstm_out, bilstm_out.size(2)).squeeze(2)
        bilstm_out = F.tanh(bilstm_out)
        # bilstm_out = self.dropout(bilstm_out)

        # bilstm_out = self.hidden2label1(bilstm_out)
        # logit = self.hidden2label2(F.tanh(bilstm_out))

        logit = self.hidden2label(bilstm_out)

        return logit