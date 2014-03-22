import re
import os
import random
from collections import defaultdict
# from itertools import chain
import logging

# create logger
module_logger = logging.getLogger('make_temp_rel_const_table')


class Node:

    """A class that stores node information."""

    def __init__(self, nodeID=None):

        self.logger = logging.getLogger('Node')
        if nodeID is None:
            self.nodeID = random.random()
        else:
            self.nodeID = nodeID


class ConstraintNetwork:

    def __init__(self, transitive_table=None, constraints=None):

        cwd = os.path.dirname(os.path.realpath(__file__))
        parentDir = os.path.dirname(cwd)

        if transitive_table is None:
            self.transitive_table = \
                os.path.join(parentDir, 'data/transitive_table.txt')
        else:
            self.transitive_table = transitive_table

        self.logger = logging.getLogger('ConstraintNetwork')
        self.nodes = set()
        self.constraints = set()
        self.networkDict = defaultdict(dict)
        if constraints is None:
            self.constraintCalculator = \
                TransitiveConstraints(self.transitive_table)
        else:
            self.constraintCalculator = constraints

    def addDefaultLinks(self, node):

        for existingNode in self.nodes:
            self.networkDict[node][existingNode] = Link(node, existingNode)
            self.networkDict[existingNode][node] = Link(existingNode, node)

    def add(self, link):

        if link.source not in self.nodes:

            self.addDefaultLinks(link.source)
            self.nodes.add(link.source)

        if link.destination not in self.nodes:
            self.addDefaultLinks(link.destination)
            self.nodes.add(link.destination)

        self.networkDict[link.source][link.destination].relation &= \
            link.relation

        self.networkDict[link.destination][link.source].relation &= \
            TemporalRelation.inverse(link.relation)

        if (int('0', 2) ==
                self.networkDict[link.source][link.destination].relation):
            return False

        elif (int('0', 2) ==
                self.networkDict[link.destination][link.source].relation):
            return False

        else:

            return True

    def relIterator(self, relation):

        goldRelations = [TemporalRelation.BEFORE, TemporalRelation.AFTER,
                         TemporalRelation.DURING, TemporalRelation.DURING_BY,
                         TemporalRelation.OVERLAP, TemporalRelation.OVERLAP_BY,
                         TemporalRelation.MEETS, TemporalRelation.MEET_BY,
                         TemporalRelation.STARTS, TemporalRelation.STARTED_BY,
                         TemporalRelation.FINISHES,
                         TemporalRelation.FINISHED_BY,
                         TemporalRelation.EQUAL]

        for goldRel in goldRelations:

            if goldRel & relation:

                yield goldRel

    def calConstraint(self, constraint_i, constraint_j):

        new_rels = int('0', 2)

        for rel_i in self.relIterator(constraint_i):

            for rel_j in self.relIterator(constraint_j):

                derivedRel = self.constraintCalculator.basicConstraints[
                    rel_i][rel_j]

                self.logger.debug(
                    '{},{} => {}'.format(
                        TemporalRelation.relationToString(rel_i),
                        TemporalRelation.relationToString(rel_j),
                        TemporalRelation.relationToString(derivedRel)))

                new_rels |= derivedRel

        return new_rels

    def isConsistent(self):
        """
        This method runs path consistency algorithm
        and return output of the algorithm
        """

        nodePairQueue = self.makePairs(self.nodes)

        while len(nodePairQueue) > 0:
            nodePair = nodePairQueue.pop(0)
            nodeI = nodePair.pop()
            nodeJ = nodePair.pop()

            for nodeK in self.nodes:

                if nodeK == nodeI or nodeK == nodeJ:
                    continue

                constraint_k_i = self.networkDict[nodeK][nodeI].relation
                constraint_i_j = self.networkDict[nodeI][nodeJ].relation

                existingConstraint_k_j = self.networkDict[
                    nodeK][nodeJ].relation

                new_constraint_k_j = self.calConstraint(constraint_k_i,
                                                        constraint_i_j)
                self.networkDict[nodeK][nodeJ].relation = \
                    TemporalRelation.intersect(
                        self.networkDict[nodeK][nodeJ].relation,
                        new_constraint_k_j)

                if self.networkDict[nodeK][nodeJ].relation == 0:

                    return False

                if (existingConstraint_k_j !=
                        self.networkDict[nodeK][nodeJ].relation):
                    nodePairQueue.append(set([nodeK, nodeJ]))
                    self.networkDict[nodeJ][nodeK].relation = \
                        TemporalRelation.inverse(
                            self.networkDict[nodeK][nodeJ].relation)

                constraint_k_j = self.networkDict[nodeK][nodeJ].relation
                constraint_j_i = self.networkDict[nodeJ][nodeI].relation

                existingConstraint_k_i = self.networkDict[
                    nodeK][nodeI].relation

                new_constraint_k_i = self.calConstraint(constraint_k_j,
                                                        constraint_j_i)

                self.networkDict[nodeK][nodeI].relation = \
                    TemporalRelation.intersect(
                        self.networkDict[nodeK][nodeI].relation,
                        new_constraint_k_i)

                if self.networkDict[nodeK][nodeI].relation == 0:

                    return False

                if (existingConstraint_k_i !=
                        self.networkDict[nodeK][nodeI].relation):
                    nodePairQueue.append(set([nodeK, nodeI]))
                    self.networkDict[nodeI][nodeK].relation = \
                        TemporalRelation.inverse(
                            self.networkDict[nodeK][nodeI].relation)

        return True

    def makePairs(self, nodes):

        pairs = []
        for nodeI in nodes:
            for nodeJ in nodes:

                if nodeI != nodeJ and set([nodeI, nodeJ]) not in pairs:

                    pairs.append(set([nodeI, nodeJ]))

        return pairs


class TemporalRelation:

    BEFORE = int('1', 2)
    AFTER = int('10', 2)
    DURING = int('100', 2)
    DURING_BY = int('1000', 2)
    OVERLAP = int('10000', 2)
    OVERLAP_BY = int('100000', 2)
    STARTS = int('1000000', 2)
    STARTED_BY = int('10000000', 2)
    FINISHES = int('100000000', 2)
    FINISHED_BY = int('1000000000', 2)
    MEETS = int('10000000000', 2)
    MEET_BY = int('100000000000', 2)
    EQUAL = int('1000000000000', 2)
    ALL = int('1111111111111', 2)

    RELATION_TO_BIT = {'<': BEFORE,
                       '>': AFTER,
                       'd': DURING,
                       'di': DURING_BY,
                       'o': OVERLAP,
                       'oi': OVERLAP_BY,
                       's': STARTS,
                       'si': STARTED_BY,
                       'f': FINISHES,
                       'fi': FINISHED_BY,
                       'm': MEETS,
                       'mi': MEET_BY,
                       '=': EQUAL,
                       'all': ALL
                       }

    @staticmethod
    def combine(relationSet):

        bitRepr = int('0', 2)

        for indRel in relationSet:

            bitRepr |= indRel

        return bitRepr

    @staticmethod
    def inverse(relations):

        inverseRel = int('0', 2)

        if TemporalRelation.BEFORE & relations:
            inverseRel |= TemporalRelation.AFTER
        if TemporalRelation.AFTER & relations:
            inverseRel |= TemporalRelation.BEFORE
        if TemporalRelation.DURING & relations:
            inverseRel |= TemporalRelation.DURING_BY
        if TemporalRelation.DURING_BY & relations:
            inverseRel |= TemporalRelation.DURING
        if TemporalRelation.OVERLAP & relations:
            inverseRel |= TemporalRelation.OVERLAP_BY
        if TemporalRelation.STARTS & relations:
            inverseRel |= TemporalRelation.STARTED_BY
        if TemporalRelation.STARTED_BY & relations:
            inverseRel |= TemporalRelation.STARTS
        if TemporalRelation.FINISHES & relations:
            inverseRel |= TemporalRelation.FINISHED_BY
        if TemporalRelation.FINISHED_BY & relations:
            inverseRel |= TemporalRelation.FINISHES
        if TemporalRelation.MEETS & relations:
            inverseRel |= TemporalRelation.MEET_BY
        if TemporalRelation.MEET_BY & relations:
            inverseRel |= TemporalRelation.MEETS
        if TemporalRelation.EQUAL & relations:
            inverseRel |= TemporalRelation.EQUAL

        return inverseRel

    @staticmethod
    def intersect(rel1, rel2):

        return rel1 & rel2

    @staticmethod
    def relationToString(relations):

        relationStr = []

        if TemporalRelation.BEFORE & relations:
            relationStr.append('before')
        if TemporalRelation.AFTER & relations:
            relationStr.append('after')
        if TemporalRelation.DURING & relations:
            relationStr.append('during')
        if TemporalRelation.DURING_BY & relations:
            relationStr.append('during_by')
        if TemporalRelation.OVERLAP & relations:
            relationStr.append('overlap')
        if TemporalRelation.OVERLAP_BY & relations:
            relationStr.append('overlap_by')
        if TemporalRelation.STARTS & relations:
            relationStr.append('starts')
        if TemporalRelation.STARTED_BY & relations:
            relationStr.append('started_by')
        if TemporalRelation.FINISHES & relations:
            relationStr.append('finish')
        if TemporalRelation.FINISHED_BY & relations:
            relationStr.append('finish_by')
        if TemporalRelation.MEETS & relations:
            relationStr.append('meets')
        if TemporalRelation.MEET_BY & relations:
            relationStr.append('meet_by')
        if TemporalRelation.EQUAL & relations:
            relationStr.append('equal')

        return ','.join(relationStr)


class TimeMLRelation:

    TIMEML_TO_ALLEN = {'BEFORE': TemporalRelation.BEFORE,
                       'AFTER': TemporalRelation.AFTER,
                       'INCLUDES': TemporalRelation.DURING_BY,
                       'IS_INCLUDED': TemporalRelation.DURING,
                       'DURING': TemporalRelation.DURING,
                       'DURING_INV': TemporalRelation.DURING_BY,
                       'SIMULTANEOUS': TemporalRelation.EQUAL,
                       'IAFTER': TemporalRelation.MEET_BY,
                       'IBEFORE': TemporalRelation.MEETS,
                       'IDENTITY': TemporalRelation.EQUAL,
                       'BEGINS': TemporalRelation.STARTS,
                       'ENDS': TemporalRelation.FINISHES,
                       'BEGUN_BY': TemporalRelation.STARTED_BY,
                       'ENDED_BY': TemporalRelation.FINISHED_BY}


class Link:

    """
    """

    def __init__(self, source, destination, relationSet=None):

        self.logger = logging.getLogger('Link')
        self.source = source
        self.destination = destination
        self.relation = None
        if relationSet is None:
            self.relation = TemporalRelation.ALL
        else:
            # TODO
            self.relation = TemporalRelation.combine(relationSet)

    def setSource(self, source):
        self.source = source

    def setDestination(self, destination):
        self.destination = destination

    def getSource(self):
        return self.source

    def getDestination(self):
        return self.destination


class TransitiveConstraints:

    """
    """

    def __init__(self, transitive_table):

        self.logger = logging.getLogger('TransitiveConstraints')

        self.transitive_table = transitive_table

        self.logger.info('creating an instance of TransitiveConstraints')
        self.basicConstraints = defaultdict(dict)
        self.storeBasicConstraints()

    def storeBasicConstraints(self, constraintFile=None):

        self.logger.info('Start to Store basic transitivity constraints')

        if constraintFile is None:
            constraintFile = self.transitive_table

        inobj = open(constraintFile, 'r')

        for line in inobj:

            if re.search('^\s*$', line):
                continue

            fields = line.rstrip().split(',')

            srcRel = TemporalRelation.RELATION_TO_BIT[fields[0]]
            trgRel = TemporalRelation.RELATION_TO_BIT[fields[1]]
            self.basicConstraints[srcRel][
                trgRel] = self.convToBitRep(fields[2])

        inobj.close()
        self.logger.info('Finish storing basic transitivity constraints')
        return

    def convToBitRep(self, rel):

        fields = rel.split()
        bitRepr = int('0', 2)

        for indRel in fields:

            bitRepr |= TemporalRelation.RELATION_TO_BIT[indRel]

        return bitRepr

    def convRelToBinary(rel):

        if '<' == rel:
            return TemporalRelation.BEFORE
        elif '>' == rel:
            return TemporalRelation.AFTER
        elif 'd' == rel:
            return TemporalRelation.DURING
        elif 'di' == rel:
            return TemporalRelation.DURING_BY
        elif 'o' == rel:
            return TemporalRelation.OVERLAP
        elif 'oi' == rel:
            return TemporalRelation.OVERLAP_BY
        elif 'm' == rel:
            return TemporalRelation.MEETS
        elif 'mi' == rel:
            return TemporalRelation.MEET_BY
        elif 's' == rel:
            return TemporalRelation.STARTS
        elif 'si' == rel:
            return TemporalRelation.STARTED_BY
        elif 'f' == rel:
            return TemporalRelation.FINISHES
        elif 'fi' == rel:
            return TemporalRelation.FINISHED_BY
        elif '=' == rel:
            return TemporalRelation.EQUAL
        else:
            raise ValueError('Undefined relation: {}'.format(rel))

    def getBasicRels(self):

        return sorted(self.basicConstraints.keys())

    def getBasicTransitiveConstraintDict(self):

        return self.basicConstraints

    def getTransitiveRelsOfBasicRels(self, firstRel, secondRel):

        return self.basicConstraints[firstRel][secondRel]

    def calTransitivity(self, relSet1, relSet2):

        union = set()
        for rel1 in relSet1:

            for rel2 in relSet2:

                union = union.union(
                    set(self.basicConstraints[rel1][rel2].split()))

        return union

    def pathConsistency(self,):

        return

    # def _powerset(iterable):
    #     "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    #     s = list(iterable)
    #     return chain.from_iterable(
    #             combinations(s, r) for r in range(len(s) + 1))

    # def makeAllPossiblePairs(self):

    #     for relSet1 in _powerset(self.getBasicRels()):

    #         if len(relSet1) == 0:

    #             continue

    #         for relSet2 in _powerset(self.getBasicRels()):

    #             if len(relSet2) == 0:

    #                 continue

    #             self.looger.debug(' '.join(relSet1) + \
                                  # ',' + ' '.join(relSet2))
