import unittest
from make_temp_rel_const_table import *


class TestConstraintNetwork(unittest.TestCase):

    def test_makePairs(self):

        nodes = set()

        for i in range(5):

            node = Node(i+1)
            nodes.add(node)

        constraintNetwork = ConstraintNetwork()
        pairs = constraintNetwork.makePairs(nodes)

        self.assertEqual(len(pairs), 10, 'Incorrect size of generated pairs')

    def test_convToBitRep(self):

        transConstraints = TransitiveConstraints()
        self.assertEqual(transConstraints.convToBitRep('< o m d s'),
                         int('10001010101', 2))

    def test_storeBasicConstraints(self):

        transConstraints = TransitiveConstraints()
        transConstraints.storeBasicConstraints('transitive_table.txt')
        totalConstraints = \
            sum(len(transConstraints.basicConstraints[v]) for
                v in transConstraints.basicConstraints)

        self.assertEqual(totalConstraints, 169)

    def test_add(self):

        nodeI = Node()
        nodeJ = Node()
        nodeK = Node()

        link_i_j = Link(nodeI, nodeJ, set([TemporalRelation.BEFORE]))
        link_j_k = Link(nodeJ, nodeK, set([TemporalRelation.BEFORE]))

        network = ConstraintNetwork()
        network.add(link_i_j)
        self.assertEqual(len(network.nodes), 2)
        self.assertEqual(network.networkDict[nodeJ][nodeI].relation,
                         TemporalRelation.AFTER)
        network.add(link_j_k)
        self.assertEqual(len(network.nodes), 3)
        self.assertEqual(network.networkDict[nodeK][nodeJ].relation,
                         TemporalRelation.AFTER)

    def test_inverse(self):
        nodeI = Node()
        nodeJ = Node()
        link = Link(nodeI, nodeJ, set([TemporalRelation.BEFORE,
                                       TemporalRelation.MEETS]))

        inversedRel = TemporalRelation.inverse(link.relation)
        self.assertEqual(inversedRel & TemporalRelation.BEFORE, 0)
        self.assertNotEqual(inversedRel & TemporalRelation.AFTER, 0)
        self.assertEqual(inversedRel & TemporalRelation.DURING, 0)
        self.assertEqual(inversedRel & TemporalRelation.DURING_BY, 0)
        self.assertEqual(inversedRel & TemporalRelation.OVERLAP, 0)
        self.assertEqual(inversedRel & TemporalRelation.OVERLAP_BY, 0)
        self.assertEqual(inversedRel & TemporalRelation.STARTS, 0)
        self.assertEqual(inversedRel & TemporalRelation.STARTED_BY, 0)
        self.assertEqual(inversedRel & TemporalRelation.FINISHES, 0)
        self.assertEqual(inversedRel & TemporalRelation.FINISHED_BY, 0)
        self.assertEqual(inversedRel & TemporalRelation.EQUAL, 0)
        self.assertEqual(inversedRel & TemporalRelation.MEETS, 0)
        self.assertNotEqual(inversedRel & TemporalRelation.MEET_BY, 0)

    def test_isConsisten(self):

        nodeI = Node()
        nodeJ = Node()
        nodeK = Node()

        link_i_j = Link(nodeI, nodeJ, set([TemporalRelation.BEFORE]))
        link_j_k = Link(nodeJ, nodeK, set([TemporalRelation.BEFORE]))

        network = ConstraintNetwork()
        network.add(link_i_j)
        network.add(link_j_k)

        self.assertTrue(network.isConsistent())
        self.assertEqual(network.networkDict[nodeI][nodeK].relation,
                         TemporalRelation.BEFORE)
        self.assertEqual(network.networkDict[nodeK][nodeI].relation,
                         TemporalRelation.AFTER)

    def test_isConsistent2(self):

        nodeI = Node()
        nodeJ = Node()
        nodeK = Node()

        link_i_j = Link(nodeI, nodeJ,
                        set([TemporalRelation.DURING,
                             TemporalRelation.STARTS,
                             TemporalRelation.FINISHES]))
        link_j_k = Link(nodeJ, nodeK,
                        set([TemporalRelation.BEFORE,
                             TemporalRelation.MEETS]))

        network = ConstraintNetwork()
        network.add(link_i_j)
        network.add(link_j_k)

        self.assertTrue(network.isConsistent())

        relationStr = TemporalRelation.relationToString(
            network.networkDict[nodeI][nodeK].relation)
        msg = "Relation is {}".format(relationStr)
        self.assertEqual(network.networkDict[nodeI][nodeK].relation,
                         TemporalRelation.BEFORE | TemporalRelation.MEETS,
                         msg)

if __name__ == "__main__":

    unittest.main()
