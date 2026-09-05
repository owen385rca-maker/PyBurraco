
import sys

import random
import math

import matplotlib.pyplot as plt

import numpy as np


import copy

from multiprocessing import Process, Queue, freeze_support



from colorama import Fore, Back, Style


#----------------------------------------

class group :

   def __init__(self, cards, is_a_run, still_in_hand) :

      self.cards = cards
      self.is_a_run = is_a_run
      self.still_in_hand = still_in_hand
      self.wc_card_number = 0

      self.cards.sort()

      self.suit = 0
      if self.is_a_run :
         self.suit = get_suit( self.cards[0] )

      self.has_wildcard = False
      for pc in cards:
         if count_deployed_wildcard( cards ) > 0 :
            self.has_wildcard = True

   def is_duplicate( g ) :
      if self.cards == g.cards :
         return True
      else :
         return False


   def print_group(self) :
      print('(', end='')
      for pc in self.cards :
         d = get_deck(pc)
         if d == 0 or d == 3 :
            print(' %.5f ' % pc, end='')
         else :
            print(' %d ' % pc, end='')
      print(') ', end='')
      if self.still_in_hand : print('h', end='')
      if self.has_wildcard : print('w', end='')
      if self.is_a_run :
         print('r', end='')
      else :
         print('n', end='')
      print()


   def print_group2(self) :
      if self.is_a_run :
         s = get_suit( self.cards[0] )
         print('  run, suit %d : ' % s, end='')
         print(Fore.RED, end='')
         print('(', end='')
         for pc in self.cards :
            d = get_deck( pc )
            if d == 0 : print(Back.GREEN, end='')
            elif d == 3 : print(Back.CYAN, end='')
            else: print(Back.RESET, end='')
            c = get_card( pc )
            if c == 1 : card_str = ' A '
            elif c < 11 : card_str = '%2d ' % c
            elif c == 11 : card_str = ' J '
            elif c == 12 : card_str = ' Q '
            elif c == 13 : card_str = ' K '
            elif c == 14 : card_str = ' A '
            print('%s' % card_str, end='' )
         print( Back.RESET, end='' )
         print(')   -  ', end='')
         print( Fore.BLACK, end='' )
         self.print_group()
      else :
         c = get_card( self.cards[0] )
         if c == 1 : card_str = ' A '
         elif c < 11 : card_str = '%2d ' % c
         elif c == 11 : card_str = ' J '
         elif c == 12 : card_str = ' Q '
         elif c == 13 : card_str = ' K '
         elif c == 14 : card_str = ' A '
         print('  nofakind,  card %s - ' % card_str, end='' )
         print(Fore.BLUE, end='')
         print('[', end='')
         for pc in self.cards :
            d = get_deck( pc )
            if d == 0 : print(Back.GREEN, end='')
            elif d == 3 : print(Back.CYAN, end='')
            else: print(Back.RESET, end='')
            print(' %d ' % pc, end='' )
         print( Back.RESET, end='' )
         print(']', end='')
         print( Fore.BLACK, end='' )
         print()






   def first_card(self) :
      return get_card( self.cards[0] )


   def last_card(self) :
      return get_card( self.cards[-1] )


   def is_card_addable(self, pc ) :

      c = get_card( pc )

      if not self.is_a_run :
         gc = get_card( self.cards[0] )
         if c == gc : return True

      s = get_suit( pc )
      if s != self.suit : return False

      fc = self.first_card()
      lc = self.last_card()

      if c == (fc-1) : return True
      if c == (lc+1) : return True

      return False


   def can_card_replace_deployed_wc(self, pc ) :
      if not self.has_wildcard : return False
      if not self.is_a_run : return False
      gr_suit = get_suit( self.cards[0] )
      pc_suit = get_suit( pc )
      if pc_suit != gr_suit : return False
      pc_card_number = get_card( pc )
      for gpc in self.cards :
         if not is_deployed_wildcard( gpc ) : continue
         gpc_card_number = get_card( gpc )
         if gpc_card_number == pc_card_number : return True
      return False



#----------------------------------------

class player :

   def __init__(self, hand, name) :
      self.hand = list(hand)
      self.group_list = []
      self.wildcard_identity = {}
      self.board_groups = []
      self.name = str(name)
      self.down = False


   def setup_initial_group_list(self, decks, rng) :
      self.group_list = check_for_groups( self.hand, verb_level=0 )
      joker_list = get_jokers( self.hand )
      joker_group_list, self.hand, self.wildcard_identity = check_for_wc_groups( joker_list, self.hand, self.group_list, decks, self.wildcard_identity, rng, verb_level=0 )
      two_list = get_twos( self.hand, self.group_list, self.wildcard_identity )
      two_group_list, self.hand, self.wildcard_identity = check_for_wc_groups( two_list, self.hand, self.group_list, decks, self.wildcard_identity, rng, verb_level=0 )
      self.group_list = check_for_groups( self.hand, verb_level=0 )


   def print_state(self) :
      print('\n  +++++++ State for player %s ++++++++++++++++++++++\n' % self.name )
      print_hand4( self.hand, self.group_list, self.wildcard_identity )
      if len(self.group_list) > 0 :
         print(' In hand groups:')
         for gr in self.group_list:
            gr.print_group2()
      if self.down :
         print(' Have gone down')
         print(' board groups:')
         for gr in self.board_groups:
            gr.print_group2()
         total_points, burraco_points, card_points  = calc_board_points( self.board_groups )
         print('    total points: %d,  burraco points %d,  card points %d' % (total_points, burraco_points, card_points) )
      else :
         print(' Still up')
      print('  ++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n')

#----------------------------------------
def clone_group( group_to_clone ) :
   clone_of_group = group( list(group_to_clone.cards), group_to_clone.is_a_run, group_to_clone.still_in_hand )
   return clone_of_group


#----------------------------------------
def clone_player( player_to_clone, name ) :

   clone_of_player = player( player_to_clone.hand, name )

   clone_of_player.wildcard_identity = copy.deepcopy( player_to_clone.wildcard_identity )
   clone_of_player.down = player_to_clone.down

   for gr in player_to_clone.group_list :
      clone_of_player.group_list.append( clone_group( gr ) )

   for gr in player_to_clone.board_groups :
      clone_of_player.board_groups.append( clone_group( gr ) )

   return clone_of_player


#----------------------------------------

def add_cards_with_wc_to_board_groups( player, **kwargs ) :

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   hand = player.hand
   board_groups = player.board_groups
   hand_groups = player.group_list

   cards_not_in_group = get_cards_not_in_group( hand, hand_groups )

   hand_wc_list = []
   for pc in cards_not_in_group :
      s = get_suit( pc )
      if s == 0 : hand_wc_list.append( pc )
      c = get_card( pc )
      if c == 2 : hand_wc_list.append( pc )

   for pc in hand_wc_list :
      cards_not_in_group.remove( pc )

   if len(hand_wc_list) == 0 :
      if verb_level > 0 :
         print('   add_cards_with_wc_to_board_groups : no wc in hand.  returning.' )
         print('       hand : ',  end='' )
         print( hand )
      return 0

   n_board_groups_no_wc = 0
   for gr in board_groups :
      if gr.has_wildcard : continue
      n_board_groups_no_wc = n_board_groups_no_wc + 1

   if n_board_groups_no_wc == 0 :
      if verb_level > 0 :
         print('   add_cards_with_wc_to_board_groups : no groups without wildcards.  returning.' )
      return 0


   for wcpc in hand_wc_list :

      candidate_old_new_group_pairs = []

      if verb_level > 0 :
         print('  add_cards_with_wc_to_board_groups :  tyring to place this wc - %d ' % wcpc )

      for gr in board_groups :

         if gr.has_wildcard : continue

         if len(gr.cards) >= 7 : continue  # don't mess up a clean burraco

         if verb_level > 0 :
            print('  add_cards_with_wc_to_board_groups :  considering adding to this group - ', end='' )
            gr.print_group()

         if gr.is_a_run :

            gr_first_cn = gr.first_card()
            gr_last_cn = gr.last_card()
            gr_suit = get_suit( gr.cards[0] )

            found_a_sandwich = False
            for hpc in cards_not_in_group :
               s = get_suit( hpc )
               if s != gr_suit :  continue
               cn = get_card( hpc )
               if cn == (gr_first_cn - 2) or cn == (gr_last_cn + 2) :
                  if verb_level > 0 : print('     add_cards_with_wc_to_board_groups:  can make a sandwich with %d and wc' % hpc )
                  fake_card = -1
                  if cn == (gr_first_cn - 2) :
                     fake_card = gr_suit*1000 + (cn + 1)*10
                  elif cn == (gr_last_cn + 2) :
                     fake_card = gr_suit*1000 + (cn - 1)*10
                  if get_deck(wcpc) > 0 : fake_card = fake_card + 3
                  fake_card_with_true_id_encoded = make_fake_card_pc_with_true_id_encoded( fake_card, wcpc )
                  candidate_group_cards = list( gr.cards )
                  candidate_group_cards.append( fake_card_with_true_id_encoded )
                  candidate_group_cards.append( hpc )
                  candidate_group_cards.sort()
                  is_a_run = True
                  still_in_hand = False
                  candidate_group = group( candidate_group_cards, is_a_run, still_in_hand )
                  candidate_old_new_group_pairs.append( (len(candidate_group.cards), gr, candidate_group, wcpc, fake_card_with_true_id_encoded ) )
                  if verb_level > 0 : candidate_group.print_group()
                  found_a_sandwich = True

            if not found_a_sandwich :
               if verb_level > 0 : print('      add_cards_with_wc_to_board_groups :  no sandwich group candidates.  add simple extension.')
               fake_card_cn = -1
               if gr_first_cn == 1 :
                  fake_card_cn = gr_last_cn + 1
               elif gr_last_cn == 14 :
                  fake_card_cn = gr_first_cn - 1
               elif abs(gr_first_cn-7) < abs(gr_last_cn-7) :
                  fake_card_cn = gr_first_cn - 1
               else :
                  fake_card_cn = gr_last_cn + 1
               if verb_level > 0 : print('      add_cards_with_wc_to_board_groups : gr first cn %d, gr last cn %d, fake card number %d' % (gr_first_cn, gr_last_cn, fake_card_cn) )
               if fake_card_cn >= 1 and fake_card_cn <= 14 :
                  fake_card = gr_suit*1000 + fake_card_cn*10
                  if get_deck(wcpc) > 0 : fake_card = fake_card + 3
                  fake_card_with_true_id_encoded = make_fake_card_pc_with_true_id_encoded( fake_card, wcpc )
                  candidate_group_cards = list( gr.cards )
                  candidate_group_cards.append( fake_card_with_true_id_encoded )
                  candidate_group_cards.sort()
                  is_a_run = True
                  still_in_hand = False
                  candidate_group = group( candidate_group_cards, is_a_run, still_in_hand )
                  candidate_old_new_group_pairs.append( (len(candidate_group.cards), gr, candidate_group, wcpc, fake_card_with_true_id_encoded) )
                  if verb_level > 0 : candidate_group.print_group()

         else :

            if verb_level > 0 : print('      add_cards_with_wc_to_board_groups :  extension of nofakind.')

            gr_cn = gr.first_card()

            fake_card = 1000 + gr_cn*10
            if get_deck(wcpc) > 0 : fake_card = fake_card + 3
            fake_card_with_true_id_encoded = make_fake_card_pc_with_true_id_encoded( fake_card, wcpc )
            candidate_group_cards = list( gr.cards )
            candidate_group_cards.append( fake_card_with_true_id_encoded )
            candidate_group_cards.sort()
            is_a_run = True
            still_in_hand = False
            candidate_group = group( candidate_group_cards, is_a_run, still_in_hand )
            candidate_old_new_group_pairs.append( (len(candidate_group.cards), gr, candidate_group, wcpc, fake_card_with_true_id_encoded) )
            if verb_level > 0 : candidate_group.print_group()


      if len( candidate_old_new_group_pairs ) > 0 :

         sorted_candidate_old_new_group_pairs = sorted( candidate_old_new_group_pairs, key=lambda x: x[0], reverse=True )

         if verb_level > 0 :
            print('      add_cards_with_wc_to_board_groups : candidate groups' )
            for grp in sorted_candidate_old_new_group_pairs :
               print('          new group length %d, wildcard %d, fake card %d' % (grp[0], grp[3], grp[4]) )
               print('             old: ', end='' )
               grp[1].print_group()
               print('             new: ', end='' )
               grp[2].print_group()

         old_group = sorted_candidate_old_new_group_pairs[0][1]
         new_group = sorted_candidate_old_new_group_pairs[0][2]
         wcpc      = sorted_candidate_old_new_group_pairs[0][3]
         fake_card_with_true_id_encoded = sorted_candidate_old_new_group_pairs[0][4]

         hand.remove( wcpc )
         player.wildcard_identity[wcpc] = fake_card_with_true_id_encoded
         if old_group not in board_groups :
            print(' *** where did old group go???')
            print('  old_group - ', end='' )
            old_group.print_group()
            print('  new_group - ', end='' )
            new_group.print_group()
            print('  wcpc - %d' % wcpc )
            print('  fake_card - %d, %.5f' % (fake_card_with_true_id_encoded, fake_card_with_true_id_encoded) )
            print('     board_groups:')
            for pbg in board_groups:
               pbg.print_group()
            exit()

         board_groups.remove( old_group )
         board_groups.append( new_group )

         if verb_level > 0 :
            player.print_state()

      else :

         if verb_level > 0 :
            print('      add_cards_with_wc_to_board_groups : no candidate groups' )


   return 0




#----------------------------------------

def add_cards_to_board_groups( player, **kwargs ) :

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   hand = player.hand
   board_groups = player.board_groups

   if verb_level > 0 :
      print('  add_cards_to_board_groups :  hand cards ', end='' )
      print( hand )

   n_placed = 99999
   total_placed = 0
   while n_placed != 0 :
      placed_cards_list = []
      for pc in hand :
         d = get_deck( pc )
         c = get_card( pc )
         if d == 0 or c == 2 :
            continue
         for gr in board_groups :
            if gr.is_card_addable( pc ) :
               if verb_level > 0 :
                  print('  add_cards_to_board_groups : adding %d to group ' % pc , end='' )
                  gr.print_group()
               gr.cards.append( pc )
               gr.cards.sort()
               placed_cards_list.append( pc )
               break

      for pc in placed_cards_list :
         hand.remove( pc )

      n_placed = len(placed_cards_list)
      total_placed = total_placed + n_placed

   if verb_level > 0 :
      if total_placed > 0 :
         print('   add_cards_to_board_groups : placed %d cards' % total_placed )
         player.print_state()
      else :
         print('   add_cards_to_board_groups : no cards placed' )

   return


#----------------------------------------

def sim_nturns_to_go_down( gi_player, gi_decks, q, rng, **kwargs ) :

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   maxnt = 200
   if 'maxnt' in kwargs :
      maxnt = kwargs['maxnt']

   gi_hand = gi_player.hand
   gi_board_groups = gi_player.board_groups
   gi_wildcard_identity = gi_player.wildcard_identity
   gi_down = gi_player.down

   if verb_level > 0 :
      print(' sim_nturns_to_go_down, %s, hand: ' % (gi_player.name), end='')
      print( gi_player.hand )

   for ti in range( maxnt ) :

      this_nt = ti

      gi_hand, gi_decks, gi_group_list, discard_pc = play_turn_card_from_deck( gi_hand, gi_board_groups, gi_decks, gi_wildcard_identity, rng, gi_down, gi_player, verb_level=0 )
      ncnig, ncnig_nwc = get_ncards_not_in_group( gi_hand, gi_group_list )
      nb   = count_number_of_burracos( gi_group_list )
      npoints = calc_hand_points( gi_hand, gi_group_list )
      if discard_pc == 0 :
         if verb_level > 1 :
            print('  *** discard pc is zero.')
         break

      if verb_level > 0 :
         ndwc = count_deployed_wildcard( gi_hand )
         print('\r  ave_nturns_to_go_down :  turn %3d :  hand cards %2d, nb = %2d, npoints = %4d, ndwc = %2d,  ncnig %3d' % (ti, len(gi_hand), nb, npoints, ndwc, ncnig), end='' )

      if ncnig == 0 :
         if verb_level > 0 :
            print('  going down!')
         this_nt = ti
         break

   q.put( (this_nt, nb, npoints) )

   return this_nt, nb, npoints

#----------------------------------------

def check_groups_for_clean_burraco( hand, group_list, wildcard_identity, **kwargs ) :

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   groups_to_save = []
   clean_groups = []
   other_groups = []

   for gr in group_list :

      if len(gr.cards) < 8 : continue

      wc_index = -1
      wc_pc = 0
      for i in range( len(gr.cards) ) :
         d = get_deck(gr.cards[i])
         if d == 0 or d == 3 :
            wc_index = i
            wc_pc = gr.cards[i]
            break

      if wc_index == -1 :
         return 0

      if (wc_index >= 7) or (len(gr.cards) - wc_index >= 7) :
         if verb_level > 0 :
            print('  check_groups_for_clean_burraco :  this group has a clean burraco that needs to be saved.')
            gr.print_group()
            print_hand4( hand, group_list, wildcard_identity )
         groups_to_save.append(gr)
         if (wc_index >= 7) :
            clean_cards = gr.cards[:wc_index]
            other_cards = gr.cards[wc_index:]
         else :
            clean_cards = gr.cards[(wc_index+1):]
            other_cards = gr.cards[:(wc_index+1)]
         is_a_run = True
         clean_gr = group( clean_cards, is_a_run, gr.still_in_hand )
         clean_groups.append( clean_gr )
         if len(other_cards) >= 3 :
            if verb_level > 0 :
               print('  check_groups_for_clean_burraco :  enough other cards to make a second group with the wc.')
            other_gr = group( other_cards, is_a_run, gr.still_in_hand )
            other_groups.append( other_gr )
         else :
            if verb_level > 0 :
               print('  check_groups_for_clean_burraco :  need to return deployed wildcard %d.' % wc_pc )
               for true_wildcard, fake_card in wildcard_identity.items() :
                  if fake_card == wc_pc :
                     hand.remove( fake_card )
                     if true_wildcard == 0 :
                        print('>>>>>> 1 attempting to add zero card to hand!')
                        exit()
                     hand.append( true_wildcard )
                     hand.sort()
                     wildcard_identity.pop( true_wildcard )
                     break

      if len(groups_to_save) > 0 :
         for gr in groups_to_save :
            if gr in group_list :
               group_list.remove(gr)
         group_list.extend( clean_groups )
         if len(other_groups) > 0 :
            group_list.extend( other_groups )
         if verb_level > 0 :
            print_hand4( hand, group_list, wildcard_identity )
            for gr in group_list :
               gr.print_group()


   return len(groups_to_save)


#----------------------------------------
def calc_hand_points( hand, groups ) :

   nb = 0
   nbsc = 0
   nbc = 0
   card_points = 0

   for gr in groups :
      if len(gr.cards) >= 7 :
         if count_wc( gr.cards ) > 0 :
            nb = nb + 1
         else :
            nbc = nbc + 1

   for pc in hand :
      c = get_card( pc )
      d = get_deck( pc )
      s = get_suit( pc )

      if c == 1 : card_points = card_points + 15

      if c == 2 : card_points = card_points + 20
      if d == 3 : card_points = card_points + 20

      if d == 0 : card_points = card_points + 30
      if s == 0 : card_points = card_points + 30

      if c > 2 and c < 8 :
         card_points = card_points +  5
      if c >= 8  :
         card_points = card_points + 10

   points_total = 100 * nb + 150 * nbsc + 200 * nbc + card_points

   return points_total


#----------------------------------------
def calc_board_points( board_groups ) :

   nb = 0
   nbsc = 0
   nbc = 0
   card_points = 0

   for gr in board_groups :

      if len(gr.cards) >= 7 :
         if count_wc( gr.cards ) > 0 :
            nb = nb + 1
         else :
            nbc = nbc + 1

      for pc in gr.cards :
         c = get_card( pc )
         d = get_deck( pc )
         s = get_suit( pc )

         if c == 1 : card_points = card_points + 15

         if c == 2 : card_points = card_points + 20
         if d == 3 : card_points = card_points + 20

         if d == 0 : card_points = card_points + 30
         if s == 0 : card_points = card_points + 30

         if c > 2 and c < 8 :
            card_points = card_points +  5
         if c >= 8  :
            card_points = card_points + 10

   points_total = 100 * nb + 150 * nbsc + 200 * nbc + card_points

   return points_total, (100 * nb + 150 * nbsc + 200 * nbc), card_points

#----------------------------------------
def count_number_of_burracos( groups ) :
   nb = 0
   for gr in groups :
      if len(gr.cards) >= 7 : nb = nb + 1
   return nb

#----------------------------------------

def get_true_wildcard_from_fake_card( fake_pc, wildcard_identity ) :

   for true_card, fake_card in wildcard_identity.items() :
      if fake_card == fake_pc : return true_card

   return 0






#----------------------------------------
def fix_illegal_group( group, hand, wildcard_identity, **kwargs ) :

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']


   if verb_level > 0 :
      print('\n  fix_illegal_group :  fixing illegal group - ', end='' )
      print( group.cards )
      print(' wildcard_identity ', end='' )
      print( wildcard_identity )

   wc_list = []
   for pc in group.cards :
      if is_deployed_wildcard( pc ) :
         wc_list.append( pc )

   largest_group_size = 0
   largest_group_dropped_wcpc = 0

   for wcpc in wc_list :
      if verb_level > 0 :
         print('      fix_illegal_group :  checking without wc %d' % wcpc )
      new_card_set = list( group.cards )
      new_card_set.remove( wcpc )
      new_gr_list = build_groups_for_suit( new_card_set, get_suit( wcpc ) )
      if len(new_gr_list) > 0 :
         for ngr in new_gr_list :
            if len(ngr.cards) > largest_group_size :
               largest_group_size = len(ngr.cards)
               largest_group_dropped_wcpc = wcpc
            if verb_level > 0 :
               print( ngr.cards )
         if verb_level > 0 :
            print('      fix_illegal_group : without wc %d found %d alternative groups' % (wcpc, len(new_gr_list)) )
      else :
         if verb_level > 0 :
            print('      fix_illegal_group : without wc %d no alternative groups found' % (wcpc) )

   if verb_level > 0 :
      print('   fix_illegal_group : dropped wildcard %d has longest group of %d.  Returning it to hand.' % (largest_group_dropped_wcpc, largest_group_size) )

   if largest_group_dropped_wcpc not in hand :
      print('   ***** fix_illegal_group : largest_group_dropped_wcpc not in hand.  %d' % largest_group_dropped_wcpc )
      print('             hand: ', end='')
      print( hand )
      return 0

   hand.remove( largest_group_dropped_wcpc )
   true_wildcard = get_true_wildcard_from_fake_card( largest_group_dropped_wcpc, wildcard_identity )
   if true_wildcard == 0 :
      print('>>>>>> 2 fix_illegal_group : attempting to add zero card to hand!')
      print('  largest_group_dropped_wcpc %d' % largest_group_dropped_wcpc )
      print('  wildcard_identity : ', end='')
      print( wildcard_identity )
      exit()
   hand.append( true_wildcard )
   hand.sort()
   if true_wildcard in wildcard_identity :
      wildcard_identity.pop( true_wildcard )
   else :
      print("\n\n *** fix_illegal_group : true_wildcard not in wildcard_identity.pop??? true = %d, fake = %d" % (true_wildcard, largest_group_dropped_wcpc ) )
      for tw, fc in wildcard_identity.items() :
         print('  true %d, fake %d' % (tw, fc ) )
      print(' hand : ', end='')
      print( hand )
      print_hand4(hand,[], wildcard_identity)


   return 0






#----------------------------------------
def count_deployed_wildcard( hand ) :
   ndwc = 0
   for pc in hand :
      d = get_deck( pc )
      if d == 0 or d == 3 : ndwc = ndwc + 1
   return ndwc

#----------------------------------------
def is_deployed_wildcard( pc ) :
   d = get_deck( pc )
   if d == 0 or d == 3 : return True
   return False

#----------------------------------------
def is_group_in_list( gr, gr_list ) :
   for g in gr_list :
      if g.is_duplicate( gr ) :
         return True
   return False

#----------------------------------------
def count_wc( hand ) :
   nwc = 0
   for pc in hand :
      d = get_deck( pc )
      if d == 0 or d == 3 : nwc = nwc + 1
   return nwc

#----------------------------------------
def get_card_duplicates_in_suit( hand, suit ) :
   cis = get_cards_in_suit( hand, suit, ignore_twos=True )
   duplicates = []
   if len(cis) <= 1 :
      return duplicates
   prev_card_number = -1
   for pc in cis :
      c = get_card( pc )
      if c == prev_card_number :
         duplicates.append( pc )
      prev_card_number = c
   return duplicates

#----------------------------------------
def check_if_group_already_in_list( group, group_list ) :
   if len(group_list) == 0 : return False
   for gr in group_list :
      if gr.cards == group.cards :
         return True
   return False

#----------------------------------------
def count_deck_zero( hand ) :
   ndz = 0
   for pc in hand :
      if get_deck( pc ) == 0 :
         ndz = ndz + 1
   return ndz
#----------------------------------------
def count_deck_three( hand ) :
   ndt = 0
   for pc in hand :
      if get_deck( pc ) == 3 :
         ndt = ndt + 1
   return ndt

#----------------------------------------
def get_jokers( hand ) :
   joker_list = []
   for pc in hand :
      s = get_suit( pc )
      if s == 0 :
         joker_list.append( pc )
   return joker_list

#----------------------------------------
def get_twos( hand, group_list, wildcard_identity ) :
   twos_list = []
   for pc in hand :
      c = get_card( pc )
      if c == 2 :
         if not is_in_a_group( pc, group_list ) :
            if pc not in wildcard_identity :
               twos_list.append( pc )
   return twos_list

#----------------------------------------
def is_in_a_group( pc, groups ) :
   for gr in groups:
      if pc in gr.cards : return True
   return False

#----------------------------------------
def get_group( pc, groups ) :
   for gr in groups:
      if pc in gr.cards : return gr
   return 0

#----------------------------------------
def get_ncards_not_in_group( hand, groups ) :
   nc = 0
   nc_not_wildcard = 0
   for pc in hand :
      if not is_in_a_group( pc, groups ) :
         nc = nc + 1
         c = get_card( pc )
         d = get_deck( pc )
         s = get_suit( pc )
         is_wc = False
         if c == 2 : is_wc = True
         if d == 0 or d == 3 : is_wc = True
         if s == 0 : is_wc = True
         if not is_wc : nc_not_wildcard = nc_not_wildcard + 1
   return nc, nc_not_wildcard

#----------------------------------------
def get_cards_not_in_group( hand, groups ) :
   cards_not_in_group = []
   for pc in hand :
      if not is_in_a_group( pc, groups ) :
         cards_not_in_group.append( pc )
   return cards_not_in_group

#----------------------------------------
def cards_in_seed_id( id ) :
   if seed_id == 0 : return 0
   nc = 0
   for c in range(15) :
      if id & np.power(2,c) == np.power(2,c) : nc += 1
   return nc


#----------------------------------------
def seed_id_to_str( id ) :
   idstr = ''
   for c in range(15) :
      if id & np.power(2,c) == np.power(2,c) :
         if c == 1 :
            idstr = idstr + '  A'
         elif c < 11 :
            idstr = idstr + ' %2d' % c
         elif c == 11 :
            idstr = idstr + '  J'
         elif c == 12 :
            idstr = idstr + '  Q'
         elif c == 13 :
            idstr = idstr + '  K'
         elif c == 14 :
            idstr = idstr + '  A'
      else :
         idstr = idstr + '  .'

   return idstr

#----------------------------------------
def get_seed_id( hand, suit ) :
   seed_id = 0
   if suit == 0 : return seed_id
   for pc in hand :
      s = get_suit( pc )
      if s != suit : continue
      c = get_card( pc )
      seed_id = seed_id + np.power( 2, c )
   if seed_id < 0 : seed_id = 0
   if seed_id > np.power( 2, 15 ) : seed_id = 0
   return seed_id

#----------------------------------------
def calc_hist_data_mean( ar ) :
   if len(ar) <= 1 : return 0
   sum_bh = np.sum(ar)
   sum_bhv = 0
   for bi in range(len(ar)) :
      sum_bhv = sum_bhv + bi * ar[bi]
   if sum_bh == 0 : return 0
   return sum_bhv / sum_bh

#----------------------------------------
def get_card( key ) :
   return math.floor( (key / 10) % 100 )

#----------------------------------------
def get_suit( key ) :
   return math.floor( (key / 1000) % 10  )


#----------------------------------------
def get_deck( key ) :
   return math.floor( key % 10 )

#----------------------------------------
def count_suit( hand, suit ) :
   rv = 0
   for pc in hand :
      s = get_suit( pc )
      if s == suit : rv = rv + 1
   return rv

#----------------------------------------
def get_true_card( key ) :
   return math.floor( (key*100000) % 10000 )

#----------------------------------------
def make_fake_card_pc_with_true_id_encoded( fake_card, true_pc ) :
   return fake_card + true_pc / 100000

#----------------------------------------
def get_card_from_deck( deck ) :
   if len(deck) == 0 : return 0, deck
   c = deck[-1]
   return c, deck[:-1]

#----------------------------------------
def print_hand( hand ) :
   for pc in hand :
      print(' %s ' % key_to_string( pc ), end = '' )
   print()
   return

#----------------------------------------
def get_cards_in_suit( hand, suit, **kwargs ) :
   rv = []
   ignore_twos = False
   if 'ignore_twos' in kwargs :
      ignore_twos = kwargs['ignore_twos']
   for pc in hand :
      s = get_suit( pc )
      if s == suit :
         c = get_card( pc )
         if c == 2 and ignore_twos : continue
         rv.append( pc )
   return rv

#----------------------------------------
def suit_card_in_hand( card, hand, suit ) :
   for pc in hand :
      s = get_suit( pc )
      if s != suit : continue
      c = get_card( pc )
      if c == card : return pc
   return 0

#----------------------------------------
def print_hand2( hand ) :
   njokers = count_suit( hand, 0 )
   if njokers > 0 : print(' Number of jokers : %d' % njokers )
   for s in range(1,5) :
      suit_str = ''
      for c in range(1,15) :
         if suit_card_in_hand( c, hand, s ) > 0 :
            if c == 1 :
               suit_str = suit_str + '  A'
            elif c < 11 :
               suit_str = suit_str + ' %2d' % c
            elif c == 11 :
               suit_str = suit_str + '  J'
            elif c == 12 :
               suit_str = suit_str + '  Q'
            elif c == 13 :
               suit_str = suit_str + '  K'
            elif c == 14 :
               suit_str = suit_str + '  A'
         else :
            suit_str = suit_str + '  .'
      print(' suit %d : %s' % (s, suit_str) )
   return

#----------------------------------------
def print_hand3( hand, groups ) :
   njokers = count_suit( hand, 0 )
   if njokers > 0 : print(' Number of jokers : %d' % njokers )
   for s in range(1,5) :
      suit_str = ''
      print(' suit %d : ' % s, end='')
      for c in range(1,15) :
         scih = suit_card_in_hand( c, hand, s )
         if scih > 0 :
            if is_in_a_group( scih, groups ) :
               print(Fore.RED, end='')
            else :
               print(Fore.BLACK, end='')
            if c == 1 :
               suit_str = '  A'
            elif c < 11 :
               suit_str = ' %2d' % c
            elif c == 11 :
               suit_str = '  J'
            elif c == 12 :
               suit_str = '  Q'
            elif c == 13 :
               suit_str = '  K'
            elif c == 14 :
               suit_str = '  A'
         else :
            suit_str = '  .'
         print( '%s' % suit_str, end='' )
      print(Fore.BLACK)
   return


#----------------------------------------
def print_hand4( hand, groups, wildcard_identity ) :
   njokers = count_suit( hand, 0 )
   if len(wildcard_identity) > 0 :
      print('Wildcard true identities')
      for k,v in wildcard_identity.items() :
         print(' %d is deployed as %d' % (k,v) )
   if njokers > 0 : print(' Number of jokers : %d  -- ' % njokers, end='' )
   if njokers > 0 :
      for pc in hand :
         if get_suit( pc ) == 0 : print(' %d ' % pc, end='')
   print()
   for s in range(1,5) :
      suit_str = ''
      print(' suit %d : ' % s, end='')
      prev_card = -1
      for c in range(1,15) :
         scih = suit_card_in_hand( c, hand, s )
         if scih > 0 :
            if is_in_a_group( scih, groups ) :
               gr = get_group( scih, groups )
               if gr.is_a_run :
                  print(Fore.RED, end='')
                  if scih == gr.cards[0] :
                     print('(', end='')
                  else :
                     print(' ', end='')
               else :
                  print(Fore.BLUE, end='')
                  print('[', end='')
            else :
               print(' ', end='')
               print(Fore.BLACK, end='')
            if get_deck( scih ) == 0 :
               print(Back.GREEN, end='')
            if get_deck( scih ) == 3 :
               print(Back.CYAN, end='')
            if c == 1 :
               suit_str = ' A '
            elif c < 11 :
               suit_str = '%2d ' % c
            elif c == 11 :
               suit_str = ' J '
            elif c == 12 :
               suit_str = ' Q '
            elif c == 13 :
               suit_str = ' K '
            elif c == 14 :
               suit_str = ' A '
         else :
            suit_str = '  . '
         print( '%s' % suit_str, end='' )
         end_str = ' '
         if is_in_a_group( scih, groups ) :
            gr = get_group( scih, groups )
            if scih == gr.cards[-1] and gr.is_a_run :
               end_str = ')'
            if not gr.is_a_run :
               end_str = ']'
         print('%s' % end_str, end='')
         if get_deck( scih ) == 0 :
            print(Back.RESET, end='')
         if get_deck( scih ) == 3 :
            print(Back.RESET, end='')
      cdis = get_card_duplicates_in_suit( hand, s )
      print(Fore.BLACK, end='')
      if len(cdis) > 0 :
         print(' duplicates: ', end='')
         for pc in cdis :
            if is_in_a_group( pc, groups ) :
               gr = get_group( pc, groups )
               if not gr.is_a_run :
                  print(Fore.BLUE, end='')
                  print('[%d]' % pc, end='')
            else :
               print(' %d ' % pc, end='' )
      print(Fore.BLACK)
   ncnig, ncnig_nwc = get_ncards_not_in_group( hand, groups )
   print('  hand :     %d cards,     %d cards not in groups,     %d non-wildcards not in groups' % (len(hand), ncnig, ncnig_nwc) )
   print('  hand cards : ', end='' )
   print( hand )
   points = calc_hand_points( hand, groups )
   print('     total points : %d\n' % points )
   return


#----------------------------------------
def duplicate_aces_in_position_list( hand, suit ) :
   for pc in hand :
      s = get_suit( pc )
      if s != suit : continue
      c = get_card( pc )
      if c == 1 :
         #print(' found ace: %d' % pc )
         d = get_deck( pc )
         duplicate_key = 1000*suit + 14*10 + d
         if duplicate_key not in hand :
            #print(' adding key %d' % duplicate_key )
            hand.append( duplicate_key )
         return
   return


#----------------------------------------
def seed_pattern_table( id_pattern ) :
   x = []
   y = []
   for p in range(14) :
      count = 0
      ave_nturns = 0
      if id_pattern in seed_id_count : count = seed_id_count[id_pattern]
      if id_pattern in ave_nturn_by_seed_id : ave_nturns = ave_nturn_by_seed_id[id_pattern]
      print('  %6d,  %10s -- %5.1f  %6d' % (id_pattern, seed_id_to_str(id_pattern), ave_nturns, count) )
      if ave_nturns > 0 :
         x.append(p)
         y.append(ave_nturns)
      id_pattern = 2 * id_pattern
      if id_pattern & np.power(2,15) != 0 : break
   return x, y


#----------------------------------------
def max_consecutive_count( hand, suit ) :
   hand.sort()
   previous_card = -1
   best_count = 0
   count = 1
   first_card = 0
   best_first_card = 0
   for pc in hand :
      s = get_suit( pc )
      if s != suit : continue
      c = get_card( pc )
      if first_card == 0 : first_card = c
      #if c < 3 : continue
      if c == previous_card : continue
      if c == (previous_card + 1) :
         count = count + 1
         if count > best_count :
            best_count = count
            best_first_card = first_card
      else :
         count = 1
         first_card = c
      previous_card = c
   return best_count, best_first_card

#----------------------------------------
def max_consecutive_count_with_wc2( hand, suit ) :

   hand.sort()
   suit_cards = []
   for pc in hand :
      s = get_suit( pc )
      if s != suit : continue
      c = get_card( pc )
      suit_cards.append(c)
   wc_candidate_positions = []
   #print(' suit cards: ', end='')
   #print( suit_cards )
   for i in range(1,14) :
      if i in suit_cards : continue
      if (i-1) in suit_cards or (i+1) in suit_cards :
         #print(' %d is candidate wc position.' % i )
         wc_candidate_positions.append(i)

   best_count = 0
   best_first_card = 0
   best_wc_card = 0
   for wcc in wc_candidate_positions :
      #print(' checking wc position %d' % wcc )
      hand_with_wc = list(hand)
      wcc_key = suit*1000 + 10*wcc
      hand_with_wc.append(wcc_key)
      hand_with_wc.sort()
      bc, bfc = max_consecutive_count( hand_with_wc, suit )
      if bc > best_count :
         best_count = bc
         best_first_card = bfc
         best_wc_card = wcc

   return best_count, best_first_card, best_wc_card





#----------------------------------------
def best_run( hand ) :
   hand.sort()
   best_suit = 0
   best_count = 0
   best_first_card = 0
   best_suit = 0
   for suit in range(5) :
      sc = count_suit( hand, suit )
      if suit == 0 : continue
      mcc, fc = max_consecutive_count( hand, suit )
      #print('   suit %d count : %d, max consecutive = %d, first card %d' % (suit, sc, mcc, fc ) )
      if mcc > best_count :
         best_count = mcc
         best_first_card = fc
         best_suit = suit
      elif mcc == best_count :
         diff1 = abs( best_first_card - 8 )
         diff2 = abs( fc - 8 )
         if diff2 < diff1 :
            best_count = mcc
            best_first_card = fc
            best_suit = suit
   #print('\n  best_suit %d, best_count %d, best first card %d\n\n' % (best_suit, best_count, best_first_card) )
   return best_suit, best_count, best_first_card


#----------------------------------------
def build_run( hand, suit, decks, min_run_length=7 ) :

   pc_in_suit = []
   n_wildcards = 0
   for pc in hand :
      s = get_suit( pc )
      if s == suit :
         pc_in_suit.append( pc )
      if s == 0 :
         n_wildcards = n_wildcards + 1
      c = get_card( pc )
      if c == 2 :
         n_wildcards = n_wildcards + 1

   if n_wildcards > 0 :
      count, fc, wc_card = max_consecutive_count_with_wc2( pc_in_suit, suit )
      #print(' %4d: count %d, first card %d, wildcard %d' % ( n_turns, count, fc, wc_card ) )
   else :
      count, fc          = max_consecutive_count( pc_in_suit, suit )
      #print(' %4d: count %d, first card %d' % ( n_turns, count, fc ) )

   if count >= min_run_length :
      #print('  build_run :  suit %d already has a run of length %d' % (suit, count) )
      return 0, fc, count

   #print_hand( pc_in_suit )

   run_length = 0
   n_turns = 0
   first_card = 0
   while run_length < min_run_length and len( decks ) > 0 :

      n_turns = n_turns + 1

      pc, decks = get_card_from_deck( decks )
      if pc == 0 :
         print('\n\n ======== no more cards!\n\n' )
         exit()

      s = get_suit( pc )
      c = get_card( pc )

      if s == 0 or c == 2 :
         n_wildcards = n_wildcards + 1

      if s != suit : continue

      #print(' adding %d ' % pc )
      pc_in_suit.append( pc )

      if c == 1 :
         #print(' duplicating ace position in hand  %d' % pc )
         d = get_deck( pc )
         duplicate_key = 1000*s + 14*10 + d
         if duplicate_key not in pc_in_suit :
            pc_in_suit.append( duplicate_key )

      if n_wildcards > 0 :
         count, fc, wc_card = max_consecutive_count_with_wc2( pc_in_suit, suit )
         #print(' %4d: count %d, first card %d, wildcard %d' % ( n_turns, count, fc, wc_card ) )
      else :
         count, fc          = max_consecutive_count( pc_in_suit, suit )
         #print(' %4d: count %d, first card %d' % ( n_turns, count, fc ) )

      run_length = count
      first_card = fc

      #print_hand( pc_in_suit )



   return n_turns, first_card, run_length


#----------------------------------------
def build_run_no_wc( hand, suit, decks, min_run_length=7 ) :

   pc_in_suit = []
   for pc in hand :
      s = get_suit( pc )
      if s == suit :
         pc_in_suit.append( pc )

   count, fc          = max_consecutive_count( pc_in_suit, suit )
   #print(' %4d: count %d, first card %d' % ( n_turns, count, fc ) )

   if count >= min_run_length :
      #print('  build_run :  suit %d already has a run of length %d' % (suit, count) )
      return 0, fc, count

   #print_hand( pc_in_suit )

   run_length = 0
   n_turns = 0
   first_card = 0
   while run_length < min_run_length and len( decks ) > 0 :

      n_turns = n_turns + 1

      pc, decks = get_card_from_deck( decks )
      if pc == 0 :
         print('\n\n ======== no more cards!\n\n' )
         exit()

      s = get_suit( pc )
      c = get_card( pc )


      if s != suit : continue

      #print(' adding %d ' % pc )
      pc_in_suit.append( pc )

      if c == 1 :
         #print(' duplicating ace position in hand  %d' % pc )
         d = get_deck( pc )
         duplicate_key = 1000*s + 14*10 + d
         if duplicate_key not in pc_in_suit :
            pc_in_suit.append( duplicate_key )

      count, fc          = max_consecutive_count( pc_in_suit, suit )
      #print(' %4d: count %d, first card %d' % ( n_turns, count, fc ) )

      run_length = count
      first_card = fc

      #print_hand( pc_in_suit )



   return n_turns, first_card, run_length


#----------------------------------------
def key_to_string( key ) :
   s = get_suit( key )
   c = get_card( key )
   d = get_deck( key )
   s_str = ''
   if s == 1 : s_str = 'c'
   if s == 2 : s_str = 'd'
   if s == 3 : s_str = 'h'
   if s == 4 : s_str = 's'
   if s == 0 : s_str = 'w'
   c_str = '%d' % c
   if c == 11 : c_str = 'J'
   if c == 12 : c_str = 'Q'
   if c == 13 : c_str = 'K'
   if c == 1  : c_str = 'A'
   if c == 14 : c_str = 'A'
   d_str = ''
   if d == 1 : d_str = 'b'
   if d == 2 : d_str = 'r'

   card_str = s_str + c_str + '_' + d_str

   #print('  key_to_string : key = %5d,  s = %d (%s),  c = %2d (%2s), deck = %d (%s), card %5s' % ( key, s, s_str, c, c_str, d, d_str, card_str ) )

   return card_str

#----------------------------------------

def get_fresh_decks( rng ) :

   decks = []

   for d in range(1,3) :
      for s in range(1,5) :
         for c in range(1,14) :
            key = 1000*s + 10*c + d
            #print('      suit %d, card %2d, deck %d key %4d' % (s,c,d,key) )
            decks.append( key )
      #-- jokers
      key = 300+d
      decks.append( key )
      key = 310+d
      decks.append( key )

   rng.shuffle( decks )

   return decks

#----------------------------------------

def calc_ave_nturns_for_suit( hand, suit, decks, rng, **kwargs ) :

   ntimes = 1000
   if 'ntimes' in kwargs :
      ntimes = kwargs['ntimes']

   min_run_length = 7
   if 'min_run_length' in kwargs :
      min_run_length = kwargs['min_run_length']

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   nturns_counts = np.zeros( shape=(200) )

   if verb_level > 0 :
      print(' calc_ave_nturns_for_suit suit %d, hand : ' % suit, end='' )
      print( hand )

   for gi in range(ntimes) :

      decks_copy = list(decks)
      rng.shuffle( decks_copy )
      n_turns, first_card, run_length = build_run( hand, suit, decks_copy, min_run_length )

      if verb_level > 0 :
         print(' gi %5d, n_turns = %3d' % (gi, n_turns) )

      nturns_counts[ n_turns ] = nturns_counts[ n_turns ] + 1

   ave_nturns = calc_hist_data_mean( nturns_counts )

   return ave_nturns

#----------------------------------------

def calc_ave_nturns_for_suit_no_wc( hand, suit, decks, rng, **kwargs ) :

   ntimes = 1000
   if 'ntimes' in kwargs :
      ntimes = kwargs['ntimes']

   min_run_length = 7
   if 'min_run_length' in kwargs :
      min_run_length = kwargs['min_run_length']

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   nturns_counts = np.zeros( shape=(200) )

   if verb_level > 0 :
      print(' calc_ave_nturns_for_suit suit %d, hand : ' % suit, end='' )
      print( hand )

   for gi in range(ntimes) :

      decks_copy = list(decks)
      rng.shuffle( decks_copy )
      n_turns, first_card, run_length = build_run_no_wc( hand, suit, decks_copy, min_run_length )

      if verb_level > 0 :
         print(' gi %5d, n_turns = %3d' % (gi, n_turns) )

      nturns_counts[ n_turns ] = nturns_counts[ n_turns ] + 1

   ave_nturns = calc_hist_data_mean( nturns_counts )

   return ave_nturns

#----------------------------------------

def get_worst_card( hand, suit, decks, group_list, ntimes, rng, **kwargs ) :

   worst_card = 0

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   worst_can_be_wc = False
   if 'worst_can_be_wc' in kwargs :
      worst_can_be_wc = kwargs['worst_can_be_wc']

   nc = count_suit( hand, suit )
   if nc == 0 : return 0

   if nc == 1 :
      for pc in hand :
         s = get_suit( pc )
         if s != suit : continue
         c = get_card( pc )
         d = get_deck( pc )
         if c == 2 and not worst_can_be_wc :
            if verb_level > 0 :
               print('  get_worst_card : only one card and it is a 2')
            return 0
         elif d == 0 or d == 3 :
            if verb_level > 0 :
               print('  get_worst_card : only one card and it is deployed WC : %d' % pc )
               print('   how can this be???  stop!')
               exit()
            return 0
         else :
            if verb_level > 0 :
               print(' get_worst_card :  only one %d' % pc )
            return pc


   ave_nturns_list = []

   if verb_level > 0 :
      print(' hand:  %s' % str(hand) )

   for pc in hand :

      if is_in_a_group( pc, group_list ) : continue

      s = get_suit( pc )
      if s != suit : continue
      if not worst_can_be_wc :
         c = get_card( pc )
         if c == 2 : continue
         d = get_deck( pc )
         if d == 0 or d == 3 : continue


      hand_without_card = list( hand )
      hand_without_card.remove( pc )

      ave_nturns = calc_ave_nturns_for_suit( hand_without_card, suit, decks, rng, ntimes=ntimes )

      ave_nturns_list.append( (pc, ave_nturns) )

      if verb_level > 0 :
         print(' ave_nturns without card %d is %5.1f' % (pc, ave_nturns) )

   if len(ave_nturns_list) == 0 :
      if verb_level > 0 :
         print('  *** get_worst_card :  no candidates!' )
      return 0

   sorted_ave_nturns_list = sorted( ave_nturns_list, key=lambda x: x[1] )
   if verb_level > 0 :
      print(' sorted_ave_nturns_list : %s' % str(sorted_ave_nturns_list) )


   worst_card = sorted_ave_nturns_list[0][0]
   if verb_level > 0 :
      print('\n   -- selected worst card: %d\n' % worst_card )

   if verb_level > 0 :
      wcs = get_suit( worst_card )
      wcd = get_deck( worst_card )
      wcc = get_card( worst_card )
      if wcs == 0 :
         print(' *** get_worst_card : worst is a joker??? %d' % worst_card )
      if wcc == 2 :
         print(' *** get_worst_card : worst is a two %d' % worst_card )
      if wcd == 0 or wcd == 3 :
         print(' *** get_worst_card : worst is a deployed wc???  %d ' % worst_card )

   return worst_card


#----------------------------------------

def play_turn_card_from_deck( hand, board_groups, decks, wildcard_identity, rng, down, player, **kwargs ) :

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   new_pc, decks = get_card_from_deck( decks )
   if new_pc == 0 :
      #print('\n\n ======== no more cards!\n\n' )
      return hand, decks, [], 0

   if verb_level > 0 :
      print('\n    ------ play_turn_card_from_deck :  card from deck %d\n' % new_pc )

   new_cards = []
   new_cards.append( new_pc )

   hand, decks, group_list, discard_pc = play_turn_new_cards( new_cards, decks, rng, player, verb_level=verb_level )

   return hand, decks, group_list, discard_pc


#----------------------------------------

def check_for_nofakind_groups( hand, group_list, **kwargs ) :

   nofakind_groups = []

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   cards_not_in_group = get_cards_not_in_group( hand, group_list )

   if len(cards_not_in_group) <= 2 :
      return nofakind_groups

   for cn in range(1,15) :

      if cn == 2 : continue

      cn_cards = []
      for pc in cards_not_in_group :
         pccn = get_card( pc )
         if pccn == cn :
            cn_cards.append( pc )
      if len(cn_cards) >= 3 :
         if verb_level > 0 :
            print('   check_for_nofakind_groups :  found this group - ', end='' )
            print( cn_cards )
         is_a_run = False
         still_in_hand = True
         new_group = group( cn_cards, is_a_run, still_in_hand )
         nofakind_groups.append( new_group )

   if len(nofakind_groups) > 0 :
      group_list.extend( nofakind_groups )

   return nofakind_groups



#----------------------------------------

def check_for_groups( hand, **kwargs ) :

   gr_list_all_suits = []

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   nwc_limit = 1
   if 'nwc_limit' in kwargs :
      nwc_limit = kwargs['nwc_limit']

   hand.sort()

   for s in range(1,5) :

      gr_list = build_groups_for_suit( hand, s, verb_level=verb_level, nwc_limit=nwc_limit )

      gr_list_all_suits.extend( gr_list )

   return gr_list_all_suits



#----------------------------------------

def check_for_wc_groups( wc_list, hand, group_list, decks, wildcard_identity, rng, **kwargs ) :

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']



   if len(wc_list) == 0 :
      return [], hand, wildcard_identity

   added_wc_groups = []

   used_wc_list = []

   for wc_pc in wc_list :

      if verb_level > 0 :
         print('---- check_for_wc_groups: checking wc %d' % wc_pc )

      wc_is_two = False
      if get_card( wc_pc ) == 2 : wc_is_two = True

      new_wc_groups = []

      for suit in range(1,5) :

         cards_in_suit = get_cards_in_suit( hand, suit, ignore_twos=False )
         if wc_pc in cards_in_suit :
            cards_in_suit.remove( wc_pc )

         if len(cards_in_suit) < 2 : continue

         for wcn in range(1,15) :


            if suit_card_in_hand( wcn, cards_in_suit, suit ) : continue

            fake_card = suit*1000 + wcn*10
            if wc_is_two : fake_card = fake_card + 3 # twos are deck 3, jokers are deck 0
            fake_card_with_true_id_encoded = make_fake_card_pc_with_true_id_encoded( fake_card, wc_pc )


            #if fake_card in cards_in_suit or (fake_card-3) in cards_in_suit :
            #   if verb_level > 0 :
            #      print('  * check_for_wc_groups: already have a wildcard with %d in hand, so skipping this.' % fake_card )
            #   continue
            for cispc in cards_in_suit :
               int_pc = math.floor(cispc)
               if int_pc == fake_card or int_pc == (fake_card-3) :
                  if verb_level > 0 :
                     print('  * check_for_wc_groups: already have a wildcard with %d in hand, so skipping this.' % fake_card )
                  continue


            temp_hand = list( cards_in_suit )
            if fake_card == 0 :
               print('>>>>>> 3 attempting to add zero card to hand!')
               exit()
            temp_hand.append( fake_card_with_true_id_encoded )
            temp_hand.sort()

            if verb_level > 0 :
               print('  check_for_wc_groups: checking suit %d, wc position %d  ' % (suit, wcn), end='' )
               print( temp_hand )

            gr_list = build_groups_for_suit( temp_hand, suit, nwc_limit=1 )

            if len(gr_list) > 0 :
               for gr in gr_list :
                  nwc = 0
                  for pc in gr.cards :
                     if get_deck(pc) == 0 or get_deck(pc) == 3 :
                        nwc = nwc + 1
                  if verb_level > 0 :
                     print(' ++ check_for_wc_groups : nwc = %d' % nwc )
                  if nwc > 1 :
                     if verb_level > 0 :
                        print('      check_for_wc_groups: this group has %d wildcards.  Skipping' % nwc, end='' )
                        print( gr.cards )
                     pass
                  else :
                     if check_if_group_already_in_list( gr, group_list ) :
                        if verb_level > 0 :
                           print('  check_for_wc_groups: group already in list: ', end='' )
                           print(gr.cards)
                     else :
                        if fake_card_with_true_id_encoded in gr.cards :
                           ncnig, ncnig_nwc = get_ncards_not_in_group( gr.cards, group_list )
                           ave_nturns = calc_ave_nturns_for_suit_no_wc( temp_hand, suit, decks, rng, ntimes=100, min_run_length=7 )
                           if verb_level > 0 :
                              print('  check_for_wc_groups: possible group for suit %d, wc position %d, n cards not in group %d, ave nt %.1f' % (suit, wcn, ncnig, ave_nturns) )
                              gr.print_group()
                           new_wc_groups.append( (ncnig, ave_nturns, gr) )


      new_wc_groups = sorted(new_wc_groups, key=lambda x: (-x[0], x[1] ) )
      for nwcg in new_wc_groups :
         if verb_level > 0 :
            print('  candidate new wc group : n cards not in group %d, ave nturns %.1f : ' % (nwcg[0], nwcg[1]), end='')
            nwcg[2].print_group()
         pass

      if len(new_wc_groups) > 0 :
         if verb_level > 0 :
            print('\n  >>>>>>>>> check_for_wc_groups : adding this group: ', end='')
            print(new_wc_groups[0][2].cards)

         nwc = count_wc( new_wc_groups[0][2].cards )
         if nwc > 1 :
            print('  *** check_for_wc_groups : 1 illegal group.  nwc = %d, cards: ' % nwc, end='')
            print( new_wc_groups[0][2].cards )
            exit()

         for ngpc in new_wc_groups[0][2].cards :
            if ngpc in used_wc_list :
               print('  *** new wc group contains a card thats already been used in another new wc group.')
               print('          card %d, wc %d, this group ' % (ngpc, wc_pc), end = '' )
               new_wc_groups[0][2].print_group()
               print('          already used wc list : ', end='' )
               print( used_wc_list )
               continue
            if ngpc in wildcard_identity.keys() :
               print('  *** this group contains %d, which is already in the wildcard_identity list.  not adding this group : ' % ngpc, end='')
               new_wc_groups[0][2].print_group()
               continue
         added_wc_groups.append( new_wc_groups[0][2] )
         group_list.append(new_wc_groups[0][2])
         hand.remove( wc_pc )
         used_wc_list.append( wc_pc )
         fake_card_with_true_id_encoded = 0
         for pc in new_wc_groups[0][2].cards :
            if wc_is_two :
               if get_deck( pc ) == 3 :
                  fake_card_with_true_id_encoded = pc
                  break
            else :
               if get_deck( pc ) == 0 :
                  fake_card_with_true_id_encoded = pc
                  break
         if fake_card_with_true_id_encoded > 0 :
            hand.append( fake_card_with_true_id_encoded )
            hand.sort()
            wildcard_identity[wc_pc] = fake_card_with_true_id_encoded
            if verb_level > 0 :
               print(' hand after adding fake card : %d, %.5f ' % (fake_card_with_true_id_encoded, fake_card_with_true_id_encoded), end='' )
               print(hand)



   return added_wc_groups, hand, wildcard_identity

#----------------------------------------
def build_groups_for_suit( hand, suit, **kwargs ) :

   gr_list = []

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   nwc_limit = 1
   if 'nwc_limit' in kwargs :
      nwc_limit = kwargs['nwc_limit']

   group_seed = []
   previous_card_number = -9

   for pc in hand :

      pcs = get_suit( pc )
      if pcs != suit : continue

      c = get_card( pc )

      if c == previous_card_number : continue

      if c == (previous_card_number+1) :
         group_seed.append( pc )
         if verb_level > 0 :
            print('       build_groups_for_suit: added to seed ', end='')
            print( group_seed )
      else :
         if len(group_seed) >= 3 :
            if verb_level > 0 :
               print('  build_groups_for_suit:  seed above threshold : ', end='' )
               print(group_seed)

            nwc = count_wc( group_seed )
            if nwc <= nwc_limit :
               is_a_run = True
               still_in_hand = True
               gr = group( group_seed, is_a_run, still_in_hand )
               if verb_level > 0 :
                  print('  build_groups_for_suit:  nwc = %d <= %d : ' % (nwc, nwc_limit) )
               gr_list.append(gr)

         group_seed = []
         group_seed.append( pc )
         if verb_level > 0 :
            print('       build_groups_for_suit: new seed ', end='')
            print( group_seed )

      previous_card_number = c

   if len(group_seed) >= 3 :
      if verb_level > 0 :
         print('  build_groups_for_suit:  seed above threshold : ', end='' )
         print(group_seed)

      nwc = count_wc( group_seed )
      if nwc <= nwc_limit  :
         if verb_level > 0 :
            print('  build_groups_for_suit:  nwc = %d <= %d : ' % (nwc, nwc_limit) )
         is_a_run = True
         still_in_hand = True
         gr = group( group_seed, is_a_run, still_in_hand )
         gr_list.append(gr)

   return gr_list



#----------------------------------------
def evaluate_pile( pile, decks, player, **kwargs ) :

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   hand = player.hand
   board_groups = player.board_groups
   group_list = player.group_list
   wildcard_identity = player.wildcard_identity
   down = player.down

   n_pile = len(pile)

   if n_pile == 1 :

      pile_pc = pile[0]

      test_hand = list( hand )
      if pile_pc == 0 :
         print('>>>>>> 4 attempting to add zero card to hand!')
         exit()
      test_hand.append( pile_pc )
      test_hand.sort()

      if verb_level > 0 :
         print('\n ----- evaluate_pile :  one card in pile - %d' % pile_pc )

      pile_suit = get_suit( pile_pc )
      pile_deck = get_deck( pile_pc )
      pile_card_number = get_card( pile_pc )

      if pile_suit == 0 :
         if verb_level > 0 :
            print('       evaluate_pile :  card is joker.  pick it up!' )
         return True

      if pile_card_number == 2 :
         if verb_level > 0 :
            print('       evaluate_pile :  card is a two.  pick it up!' )
         return True


      for gr in group_list :
         if gr.is_card_addable( pile_pc ) :
            if verb_level > 0 :
               print('       evaluate_pile :  card is addable to this group - ', end='' )
               gr.print_group()
            return True

      test_group_list = build_groups_for_suit( test_hand, pile_suit )
      if len(test_group_list) > 0 :
         for gr in test_group_list :
            if pile_pc in gr.cards :
               if verb_level > 0 :
                  print('       evaluate_pile : can create this new group with the card - ', end='' )
                  gr.print_group()
               return True

      #ng = 400
      #ng = 100
      ng = 40

      if not player.down :

         ave_nturns_no_pile = calc_ave_nturns_for_suit( hand, pile_suit, decks, rng, ntimes=ng )
         if verb_level > 0 :
            print('          evaluate_pile :  ave nturns for a run in pile suit without pile card: %.2f' % ave_nturns_no_pile )

         ave_nturns_with_pile = calc_ave_nturns_for_suit( test_hand, pile_suit, decks, rng, ntimes=ng )
         if verb_level > 0 :
            print('          evaluate_pile :  ave nturns for a run in pile suit with pile card: %.2f' % ave_nturns_with_pile )

         if ( ave_nturns_no_pile - ave_nturns_with_pile ) > 5 and ave_nturns_with_pile < 30.0 :
            if verb_level > 0 :
               print('              evaluate_pile :  delta ave turns = %.2f and ave nturns < 30..  Seems good!' % ( ave_nturns_no_pile - ave_nturns_with_pile ) )
            return True



   ####---------
   elif n_pile > 1 :

      if player.down and count_number_of_burracos( player.board_groups ) == 0 and "clone" not in player.name :
         if verb_level > 0 :
            print('  evaluate_pile : still need a burraco.  Check if we can get one with this pile by cloning player and playing a turn.' )
            print('   state of real player' )
            player.print_state()
         test_player = clone_player(player, "%s, clone" % (player.name) )
         test_player.hand.extend( pile )
         test_player.hand.sort()
         test_decks = list( decks )
         if verb_level > 0 :
            print('   state of clone player before play_turn_new_cards' )
            test_player.print_state()
         test_hand, test_decks, test_group_list, discard_pc = play_turn_new_cards( pile, test_decks, rng, test_player, verb_level=verb_level )
         test_nb = count_number_of_burracos( test_player.board_groups )
         if test_nb > 0 :
            if verb_level > 0 :
               print('         evaluate_pile : can get a burraco with this pile.  pick it up!')
            return True
         else :
            if verb_level > 0 :
               print('\n\n     evaluate_pile : no new burraco with this pile.  done with clone.\n\n' )
               print('  state of real player')
               player.print_state()
               print('   state of clone player before play_turn_new_cards' )
               test_player.print_state()

      if verb_level > 0 :
         sp = list(pile)
         sp.sort()
         print('\n ----- evaluate_pile :  sorted cards in pile - ', end=''  )
         print( sp )

      for pile_pc in pile :

         pile_suit = get_suit( pile_pc )
         pile_deck = get_deck( pile_pc )
         pile_card_number = get_card( pile_pc )

         if pile_suit == 0 and len(pile) < 4 :
            if verb_level > 0 :
               print('       evaluate_pile :  card is joker.  pick it up!' )
            return True

         if pile_card_number == 2 and len(pile) < 4 :
            if verb_level > 0 :
               print('       evaluate_pile :  card is a two.  pick it up!' )
            return True

      test_hand = list( hand )
      test_hand.extend( pile )
      test_hand.sort()

      n_pile_cards_used_in_groups = 0

      ave_nturns_hand, ave_nb_hand, ave_npoints_hand                               = ave_nturns_to_go_down( hand, board_groups, decks, wildcard_identity, down, player, verb_level=1 )

      ave_nturns_hand_with_pile, ave_nb_hand_with_pile, ave_npoints_hand_with_pile = ave_nturns_to_go_down( test_hand, board_groups, decks, wildcard_identity, down, player, verb_level=1 )

      if verb_level > 0 :
         print('       evaluate_pile : ave nturns to go down for hand without pile :    ', end='')
         print(Fore.BLUE, end='')
         print(' %6.2f' % ave_nturns_hand, end='')
         print(Fore.BLACK, end='')
         print(',    ave_nb = %6.2f,    ave_npoints = %6.1f' % (ave_nb_hand, ave_npoints_hand) )
         print('       evaluate_pile : ave nturns to go down for hand with    pile :    ', end='')
         print(Fore.BLUE, end='')
         print(' %6.2f' % ave_nturns_hand_with_pile, end='')
         print(Fore.BLACK, end='')
         print(',    ave_nb = %6.2f,    ave_npoints = %6.1f' % (ave_nb_hand_with_pile, ave_npoints_hand_with_pile) )

      if player.down :
         if ave_nturns_hand_with_pile < (ave_nturns_hand - 3.0) :
            if verb_level > 0 :
               print('       evaluate_pile :  recommend picking up the pile.' )
            return True
      else :
         if ave_nturns_hand_with_pile < (ave_nturns_hand + 2.0) :
            if verb_level > 0 :
               print('       evaluate_pile :  recommend picking up the pile.' )
            return True




   if verb_level > 0 :
      print('       evaluate_pile : nothing usable.' )

   return False

#----------------------------------------

def check_for_deployed_wc_replacement_in_board_groups( hand, board_groups, wildcard_identity, **kwargs ) :

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   hand_copy = list(hand)

   for pc in hand_copy :

      for gr in board_groups :

         if gr.can_card_replace_deployed_wc( pc ) :

            if verb_level > 0 :
               print('   check_for_deployed_wc_replacement_in_board_groups :  hand card %d can replace a wc in board group ' % pc, end='' )
               gr.print_group()

            wcpc = 0
            for gpc in gr.cards :
               if is_deployed_wildcard( gpc ) :
                  wcpc = gpc
                  break

            if wcpc == 0 :
               print(' *** check_for_deployed_wc_replacement_in_board_groups : cant find wc in group cards. ', end='')
               gr.print_group()
               break

            if pc in hand :

               hand.remove( pc )
               gr.cards.remove( wcpc )
               gr.cards.append( pc )
               gr.cards.sort()

               true_wc_pc = get_true_wildcard_from_fake_card( wcpc, wildcard_identity )
               if true_wc_pc == 0 :
                  print(' *** check_for_deployed_wc_replacement_in_board_groups : cant get true identity for deployed wc %d' % wcpc )
                  print( wildcard_identity )
                  break

               gr_first_cn = gr.first_card()
               gr_last_cn = gr.last_card()

               new_wc_cn = -1
               if gr_first_cn == 1 :
                  new_wc_cn = gr_last_cn + 1
               elif gr_last_cn == 14 :
                  new_wc_cn = gr_first_cn - 1
               elif abs(gr_first_cn-7) < abs(gr_last_cn-7) :
                  new_wc_cn = gr_first_cn-1
               else :
                  new_wc_cn = gr_last_cn+1

               new_fake_card = get_suit(gr.cards[0])*1000 + new_wc_cn*10

               if get_suit( true_wc_pc ) != 0 : new_fake_card = new_fake_card + 3

               fake_card_with_true_id_encoded = make_fake_card_pc_with_true_id_encoded( new_fake_card, true_wc_pc )

               if verb_level > 0 :
                  print('  get_suit(gr.cards[0]) = %d, gr_first_cn = %d, gr_last_cn = %d, new_fake_card = %d, true_wc_pc = %d'
                   %(get_suit(gr.cards[0]), gr_first_cn, gr_last_cn,  new_fake_card, true_wc_pc ) )

               gr.cards.append( fake_card_with_true_id_encoded )
               gr.cards.sort()

               wildcard_identity[true_wc_pc] = fake_card_with_true_id_encoded

               if verb_level > 0 :
                  print('   check_for_deployed_wc_replacement_in_board_groups : new group after replacing deployed wc - ', end='')
                  gr.print_group()

   return


#----------------------------------------

def check_for_deployed_wc_replacement_in_hand( hand, new_cards, wildcard_identity, **kwargs ) :

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   for new_pc in new_cards :

      pop_list = []
      for true_wildcard, fake_card in wildcard_identity.items() :
         c = get_card( new_pc )
         s = get_suit( new_pc )
         fc = get_card( fake_card )
         fs = get_suit( fake_card )
         if c == fc and s == fs and fake_card in hand :
            if verb_level > 0 :
               print('     *** s=%d, c=%d : this is the real card %d for spot held by wildcard %d, which is %d.' % (s, c, new_pc, fake_card, true_wildcard) )
               print('         hand before returning wc :', end='' )
               print( hand )
            if fake_card not in hand :
               print('\n *** check_for_deployed_wc_replacement_in_hand : fake_card not in hand???  fake_card %d,  hand ' % fake_card, end='' )
               print(hand)
            else :
               hand.remove( fake_card )
            if true_wildcard == 0 :
               print('>>>>>> 5 attempting to add zero card to hand!')
               exit()
            hand.append( true_wildcard )
            hand.sort()
            if verb_level > 0 :
               print('         hand after returning wc :', end='' )
               print( hand )
            pop_list.append( true_wildcard )
      if len(pop_list) > 0 :
         if verb_level > 0 :
            print('  current wildcard_identity : ', end='' )
            print(wildcard_identity)
         for pc in pop_list :
            wildcard_identity.pop(pc)
         if verb_level > 0 :
            print('  after pop(s) : ', end='' )
            print(wildcard_identity)

      if verb_level > 0 :
         print('    adding %d to hand' % new_pc )

      if new_pc == 0 :
         print('>>>>>> 6 attempting to add zero card to hand!')
         exit()
      hand.append( new_pc )
      hand.sort()

   return

#----------------------------------------

def play_turn_new_cards( new_cards, decks, rng, player, **kwargs ) :

   hand = player.hand
   board_groups = player.board_groups
   wildcard_identity = player.wildcard_identity
   down = player.down

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']


   if verb_level > 0 :
      print(' hand : ', end='' )
      print( hand )

   ncnig, ncnig_nwc = get_ncards_not_in_group( player.hand, player.group_list )

   if down :
      nburracos = count_number_of_burracos( board_groups )
      if nburracos > 0 or ncnig > 2 :
         check_for_deployed_wc_replacement_in_board_groups( hand, board_groups, wildcard_identity, verb_level=verb_level )
         add_cards_to_board_groups( player, verb_level=verb_level )
         add_cards_with_wc_to_board_groups( player, verb_level=verb_level )




   check_for_deployed_wc_replacement_in_hand( hand, new_cards, wildcard_identity, verb_level=verb_level )

   group_list = check_for_groups( hand, verb_level=0 )

   if verb_level > 1 :
      print_hand4( hand, group_list, wildcard_identity )
      if len(group_list) > 0 :
         print(' ++ group list')
         for gr in group_list :
            gr.print_group()

   joker_list = get_jokers( hand )
   #joker_group_list = check_for_wc_groups( joker_list, hand, group_list, decks, wildcard_identity, rng, verb_level=0 )
   joker_group_list = []
   for jpc in joker_list :
      tmp_joker_group_list, hand, wildcard_identity = check_for_wc_groups( [jpc], hand, group_list, decks, wildcard_identity, rng, verb_level=0 )
      if len(tmp_joker_group_list) > 0 :
         joker_group_list.extend( tmp_joker_group_list )

   if verb_level > 1 :
      if len(joker_group_list) > 0 :
         print('joker group list')
         for gr in joker_group_list :
            gr.print_group()

   two_list = get_twos( hand, group_list, wildcard_identity )
   #two_group_list = check_for_wc_groups( two_list, hand, group_list, decks, wildcard_identity, rng, verb_level=0 )
   two_group_list = []
   for tpc in two_list :
      this_two_is_already_in_a_group = False
      for cgr in group_list :
         if tpc in cgr.cards :
            this_two_is_already_in_a_group = True
            break
      if this_two_is_already_in_a_group : continue
      tmp_two_group_list, hand, wildcard_identity = check_for_wc_groups( [tpc], hand, group_list, decks, wildcard_identity, rng, verb_level=0 )
      if len(tmp_two_group_list) > 0 :
         two_group_list.extend( tmp_two_group_list )

   if verb_level > 1 :
      if len(two_group_list) > 0 :
         print('two group list')
         for gr in two_group_list :
            gr.print_group()

   nofakind_group_list = check_for_nofakind_groups( hand, group_list, verb_level=0 )
   if verb_level > 1 :
      if len(nofakind_group_list) > 0 :
         print('nofakind group list')
         for gr in nofakind_group_list :
            gr.print_group()


   if verb_level > 0 :
      print('\n Overall group list:')
      for gr in group_list :
         gr.print_group()
      print()

   if player.down and len(group_list) > 0 :
      if verb_level > 0 :
         print('   Adding these groups to board:')
      for gr in group_list :
         if verb_level > 0 :
            gr.print_group()
         gr.still_in_hand = False
         player.board_groups.append( gr )
         for pc in gr.cards :
            if pc in player.hand :
               player.hand.remove(pc)
            else :
               print('\n\n ****** trying to remove %d from hand but its not in hand!!' % pc )
               print( player.hand )
               print(' currently removing cards in hand for this group : ', end = '' )
               gr.print_group()
               player.print_state()
               print(' full list of new groups:')
               for pgr in group_list :
                  pgr.print_group()
               exit()
         player.hand.sort()
      if verb_level > 0 :
         player.print_state()


   best_run_suit, best_run_count, best_run_first_card = best_run( hand )

   if verb_level > 1 :
      print('     play_turn_new_cards :     best run suit : %d' % best_run_suit )
      print('   land length %d : ' % len(hand), end='' )
      print( hand )
      print_hand4( hand, group_list, wildcard_identity )

   ncnig, ncnig_nwc = get_ncards_not_in_group( hand, group_list )


   if ncnig == 0 :

      if verb_level > 0 :
         print('   play_turn_new_cards : all cards in groups.  Maybe we can go down without a discard.' )

      group_list = check_for_groups( hand, verb_level=0, nwc_limit=2 )
      nofakind_group_list = check_for_nofakind_groups( hand, group_list, verb_level=0 )

      if verb_level > 0 :
         print_hand4( hand, group_list, wildcard_identity )
         print(' --- group list:')
      for gr in group_list :
         if verb_level > 0 :
            gr.print_group()
         if count_wc( gr.cards ) > 1 :
            if verb_level > 0 :
               print('\n\n *** illegal group.\n\n')
            fix_illegal_group( gr, hand, wildcard_identity, verb_level=verb_level )
            group_list = check_for_groups( hand, verb_level=0 )
            if verb_level > 0 :
               print_hand4( hand, group_list, wildcard_identity )
      check_groups_for_clean_burraco( hand, group_list, wildcard_identity, verb_level=0 )
      ncnig, ncnig_nwc = get_ncards_not_in_group( hand, group_list )

      if ncnig == 0 and not player.down :
         if verb_level > 0 :
            print('   play_turn_new_cards : going down without a discard.' )
         discard_pc = 0
         return hand, decks, group_list, discard_pc


   ave_nturns_by_suit = []

   #ng = 400
   #ng = 100
   ng = 40
   ave_nturns_s1 = calc_ave_nturns_for_suit( hand, 1, decks, rng, ntimes=ng )
   if verb_level > 1 :
      print('  play_turn_new_cards :  Average n_turns for suit 1 :  %5.1f' % ave_nturns_s1 )
   ave_nturns_by_suit.append( (1,ave_nturns_s1) )

   ave_nturns_s2 = calc_ave_nturns_for_suit( hand, 2, decks, rng, ntimes=ng )
   if verb_level > 1 :
      print('  play_turn_new_cards :  Average n_turns for suit 2 :  %5.1f' % ave_nturns_s2 )
   ave_nturns_by_suit.append( (2,ave_nturns_s2) )

   ave_nturns_s3 = calc_ave_nturns_for_suit( hand, 3, decks, rng, ntimes=ng )
   if verb_level > 1 :
      print('  play_turn_new_cards :  Average n_turns for suit 3 :  %5.1f' % ave_nturns_s3 )
   ave_nturns_by_suit.append( (3,ave_nturns_s3) )

   ave_nturns_s4 = calc_ave_nturns_for_suit( hand, 4, decks, rng, ntimes=ng )
   if verb_level > 1 :
      print('  play_turn_new_cards :  Average n_turns for suit 4 :  %5.1f' % ave_nturns_s4 )
   ave_nturns_by_suit.append( (4,ave_nturns_s4) )

   sorted_ave_nturns_by_suit = sorted( ave_nturns_by_suit, key=lambda x: x[1], reverse=True )

   if verb_level > 1 :
      print( sorted_ave_nturns_by_suit )

   worst_suit = sorted_ave_nturns_by_suit[0][0]

   if verb_level > 1 :
      print('\n play_turn_new_cards :  Worst suit is %d' % worst_suit )

   if count_suit( hand, worst_suit ) == 0 :
      if verb_level > 1 :
         print(' ** suit %d has no cards.  Second worst is %d' % (worst_suit, sorted_ave_nturns_by_suit[1][0]) )
      worst_suit = sorted_ave_nturns_by_suit[1][0]

      if count_suit( hand, worst_suit ) == 0 :
         if verb_level > 1 :
            print(' **** suit %d ALSO has no cards.  Third worst is %d' % (worst_suit, sorted_ave_nturns_by_suit[2][0]) )
         worst_suit = sorted_ave_nturns_by_suit[2][0]

         if count_suit( hand, worst_suit ) == 0 :
            if verb_level > 1 :
               print(' ******* suit %d ALSO has no cards.  Fourth worst is %d' % (worst_suit, sorted_ave_nturns_by_suit[3][0]) )
            worst_suit = sorted_ave_nturns_by_suit[3][0]



   worst_can_be_wc = False
   if ncnig == 1 or ncnig_nwc == 0 :
      if verb_level > 0 :
         print('   play_turn_new_cards : allowing worst to be wc.')
      worst_can_be_wc = True

   #ng = 100
   #ng = 50
   ng = 40
   worst_card = get_worst_card( hand, worst_suit, decks, group_list, ng, rng, worst_can_be_wc=worst_can_be_wc )
   if worst_card == 0 :
      worst_suit = sorted_ave_nturns_by_suit[1][0]
      if verb_level > 1 :
         print(' Going to 2nd worst suit %d' % worst_suit )
      worst_card = get_worst_card( hand, worst_suit, decks, group_list, ng, rng, worst_can_be_wc=worst_can_be_wc )
      if worst_card == 0 :
         worst_suit = sorted_ave_nturns_by_suit[2][0]
         if verb_level > 1 :
            print(' Going to 3nd worst suit %d' % worst_suit )
         worst_card = get_worst_card( hand, worst_suit, decks, group_list, ng, rng, worst_can_be_wc=worst_can_be_wc )
         if worst_card == 0 :
            worst_suit = sorted_ave_nturns_by_suit[3][0]
            if verb_level > 1 :
               print(' Going to 4th worst suit %d' % worst_suit )
            worst_card = get_worst_card( hand, worst_suit, decks, group_list, ng, rng, worst_can_be_wc=worst_can_be_wc )



   if worst_card == 0 and ncnig > 0 and ncnig_nwc == 0 :
      if verb_level > 1 :
         print(' play_turn_new_cards : only card not in a group seems to be a wildcard.  Allowing worst card to be that card.')
      cards_not_in_group = get_cards_not_in_group( hand, group_list )
      if len(cards_not_in_group) == 1 :
         worst_card = cards_not_in_group[0]
         if verb_level > 1 :
            print('       assigning worst card to be %d' % worst_card )
      else :
         if verb_level > 1 :
            print('      cards_not_in_group has more than one card???')
            print('  hand: ', end='')
            print( hand )
            print('  cards_not_in_group: ', end='')
            print( cards_not_in_group )
         worst_card = cards_not_in_group[0]

   discard_pc = 0
   if worst_card != 0 :
      hand.remove( worst_card )
      discard_pc = worst_card


   if verb_level > 0 :
      print(' play_turn_new_cards : hand without worst card, which was %d' % worst_card )
      print(' %d : ' % len(hand), end='' )
      print( hand )

   group_list = check_for_groups( hand, verb_level=0, nwc_limit=2 )
   nofakind_group_list = check_for_nofakind_groups( hand, group_list, verb_level=0 )

   if verb_level > 0 :
      print_hand4( hand, group_list, wildcard_identity )
      print(' --- group list:')
   for gr in group_list :
      if verb_level > 0 :
         gr.print_group()
      if count_wc( gr.cards ) > 1 :
         if verb_level > 0 :
            print('\n\n *** illegal group.\n\n')
         fix_illegal_group( gr, hand, wildcard_identity, verb_level=verb_level )
         group_list = check_for_groups( hand, verb_level=0 )
         if verb_level > 0 :
            print_hand4( hand, group_list, wildcard_identity )

   n_saved = check_groups_for_clean_burraco( hand, group_list, wildcard_identity, verb_level=0 )
   if n_saved > 0 and verb_level > 0 :
      print(' *** Saved a clean burraco.')
      print_hand4( hand, group_list, wildcard_identity )
      for gr in group_list :
         gr.print_group()




   return hand, decks, group_list, discard_pc


#----------------------------------------
def ave_nturns_to_go_down( hand, board_groups, decks, wildcard_identity, down, player, **kwargs ) :

   save_hand = list(hand)
   save_board_groups = list(board_groups)
   save_decks = list(decks)
   save_wcid = copy.deepcopy(wildcard_identity)
   save_down = down
   save_player = clone_player( player, player.name )

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   ngames = 10
   if 'ngames' in kwargs :
      ngames = kwargs['ngames']

   maxnt = 200
   if 'maxnt' in kwargs :
      maxnt = kwargs['maxnt']

   nturns_hist_data = np.zeros( shape=(maxnt) )

   nb_sum = 0
   npoints_sum = 0

   q = Queue()

   procs = []

   rngs = rng.spawn( ngames )

   for gi in range( ngames ) :

      gi_decks = list(save_decks)
      gi_player = clone_player(save_player, "%s, clone %d" % (player.name, gi) )
      gi_player.hand = list( save_hand )

      rng.shuffle( gi_decks )

      proc = Process( target = sim_nturns_to_go_down, args = (gi_player, gi_decks, q, rngs[gi]) )
      procs.append( proc )
      proc.start()

   for proc in procs :
      proc.join()

   for gi in range( ngames ) :

      this_nt, this_nb, this_npoints = q.get()
      print(' %2d :  nt = %3d,  nb = %2d,  points = %4d ' % (gi, this_nt, this_nb, this_npoints) )

      nturns_hist_data[this_nt] = nturns_hist_data[this_nt] + 1
      nb_sum = nb_sum + this_nb
      npoints_sum = npoints_sum + this_npoints


   ave_nturns = calc_hist_data_mean( nturns_hist_data )
   ave_nb = nb_sum / ngames
   ave_npoints = npoints_sum / ngames

   hand = list(save_hand)
   decks = list(save_decks)
   wildcard_identity = copy.deepcopy( save_wcid )

   if verb_level > 0 :
      print('\n ave_nturns_to_go_down :  ave nturns =    %.2f   ,     ave nb = %d/%d =      %.2f ,    ave npoints =     %.1f\n' % (ave_nturns, nb_sum, ngames, ave_nb, ave_npoints) )

   return ave_nturns, ave_nb, ave_npoints


#----------------------------------------

def check_all_cards( player1, player2, decks, pile, **kwargs ) :

   verb_level = 0
   if 'verb_level' in kwargs :
      verb_level = kwargs['verb_level']

   if verb_level > 1 :

      print('\n\n ---------------- check_all_cards ----------------\n')

      player1.print_state()
      player2.print_state()
      print('  decks  %d : ' % len(decks), end='' )
      print( decks )
      print()

   all_cards = []
   all_cards.extend( decks )
   all_cards.extend( pile )
   for pc in player1.hand :
      if is_deployed_wildcard( pc ) :
         all_cards.append( get_true_wildcard_from_fake_card( pc, player1.wildcard_identity) )
      else :
         all_cards.append( pc )
   for pc in player2.hand :
      if is_deployed_wildcard( pc ) :
         all_cards.append( get_true_wildcard_from_fake_card( pc, player2.wildcard_identity) )
      else :
         all_cards.append( pc )
   if player1.down :
      for gr in player1.board_groups :
         for pc in gr.cards :
            if is_deployed_wildcard( pc ) :
               all_cards.append( get_true_wildcard_from_fake_card( pc, player1.wildcard_identity) )
            else :
               all_cards.append( pc )
   if player2.down :
      for gr in player2.board_groups :
         for pc in gr.cards :
            if is_deployed_wildcard( pc ) :
               all_cards.append( get_true_wildcard_from_fake_card( pc, player2.wildcard_identity) )
            else :
               all_cards.append( pc )
   all_cards.sort()

   if verb_level > 1 :
      print('  all cards  %d : ' % len(all_cards), end='' )
      print( all_cards )

   correct_reference = [301, 302, 311, 312, 1011, 1012, 1021, 1022, 1031, 1032, 1041, 1042, 1051, 1052, 1061, 1062, 1071, 1072, 1081, 1082, 1091, 1092, 1101, 1102, 1111, 1112, 1121, 1122, 1131, 1132, 2011, 2012, 2021, 2022, 2031, 2032, 2041, 2042, 2051, 2052, 2061, 2062, 2071, 2072, 2081, 2082, 2091, 2092, 2101, 2102, 2111, 2112, 2121, 2122, 2131, 2132, 3011, 3012, 3021, 3022, 3031, 3032, 3041, 3042, 3051, 3052, 3061, 3062, 3071, 3072, 3081, 3082, 3091, 3092, 3101, 3102, 3111, 3112, 3121, 3122, 3131, 3132, 4011, 4012, 4021, 4022, 4031, 4032, 4041, 4042, 4051, 4052, 4061, 4062, 4071, 4072, 4081, 4082, 4091, 4092, 4101, 4102, 4111, 4112, 4121, 4122, 4131, 4132]

   n_bad = 0
   for i in range(108) :
      if verb_level > 1 :
         print('  %3d :  now %4d  ,  reference %4d' % (i, all_cards[i], correct_reference[i]) )
      if all_cards[i] != correct_reference[i] :
         print('  *** check_all_cards : disagreement with reference - position %3d, %4d not %4d' % (i, all_cards[i], correct_reference[i]) )
         n_bad = n_bad + 1

   if n_bad > 0 or len( all_cards ) != 108 :
      print('  *** check_all_cards :  number of disagreements with reference %d' % n_bad )

      if len( all_cards ) != 108 :
         print('  *** check_all_cards :  currently have %d cards.  expected 108.' % len( all_cards ) )

      print('     player 1 hand, %3d cards : ' % len(player1.hand), end='' )
      print( player1.hand )
      print('     player 2 hand, %3d cards : ' % len(player2.hand), end='' )
      print( player2.hand )
      print('     pile,          %3d cards : ' % len(pile), end='' )
      print( pile )
      print('     decks,         %3d cards : ' % len(decks), end='' )
      decks_sorted = list(decks)
      decks_sorted.sort()
      print( decks_sorted )
      if player1.down :
         down_cards = []
         for gr in player1.board_groups :
            for pc in gr.cards :
               if is_deployed_wildcard( pc ) :
                  down_cards.append( get_true_wildcard_from_fake_card( pc, player1.wildcard_identity) )
               else :
                  down_cards.append( pc )
         print('    player 1 down, %3d cards : ' % len(down_cards), end='' )
         down_cards.sort()
         print( down_cards )
      if player2.down :
         down_cards = []
         for gr in player2.board_groups :
            for pc in gr.cards :
               if is_deployed_wildcard( pc ) :
                  down_cards.append( get_true_wildcard_from_fake_card( pc, player2.wildcard_identity) )
               else :
                  down_cards.append( pc )
         print('    player 2 down, %3d cards : ' % len(down_cards), end='' )
         down_cards.sort()
         print( down_cards )

      return False

   if verb_level > 0 :
      print('  check_all_cards : all good' )

   return True


#===  main  ==========================================================================================================

if __name__ == '__main__':

   freeze_support()

   print('\n\n')
   print(' Arguments:  %d' % len(sys.argv) )
   for arg in sys.argv :
      print( arg )

   if len(sys.argv) > 1 :
      seed = int(sys.argv[1])
      print('\n\n Setting random seed to %d\n\n' % seed )
      #random.seed( seed )
      rng = np.random.default_rng(seed)
   else :
      rng = np.random.default_rng()

   batch = False
   if len(sys.argv) > 2 :
      if sys.argv[2] == 'b' :
         batch = True



   #wildcard_identity = {}

   decks = get_fresh_decks( rng )

   hand1 = decks[-11:]
   decks = decks[:-11]

   hand2 = decks[-11:]
   decks = decks[:-11]

   hand1.sort()
   hand2.sort()

   player1 = player( hand1, 'one' )
   player2 = player( hand2, 'two' )

   player1.setup_initial_group_list(decks, rng)
   player2.setup_initial_group_list(decks, rng)

   player1.print_state()
   player2.print_state()



   pile = []

   check_all_cards( player1, player2, decks, pile, verb_level=1 )

   new_pc, decks = get_card_from_deck( decks )
   if new_pc == 0 :
      print('\n\n ======== no more cards!\n\n' )
      exit()

   pile.append( new_pc )
   print('\n\n')
   print(' === Pile : ', end='' )
   print( pile )





   for ti in range(1,61) :

   #-------

      print('\n\n\n ===================================== turn %2d for player %s ====================================================================\n\n' % (ti, player1.name) )

      player1.print_state()

      pickup_pile = evaluate_pile( pile, decks, player1, verb_level=1 )

      ncnig1, ncnig_nwc1 = get_ncards_not_in_group( player1.hand, player1.group_list )

      turn_cards = []
      if pickup_pile :
         print(' ***** picking up the pile ', end='' )
         print( pile )
         turn_cards.extend( pile )
         pile = []
      else :
         new_pc, decks = get_card_from_deck( decks )
         print(' card from deck: %d' % new_pc  )
         if new_pc == 0 :
            print('\n\n ======== no more cards!\n\n' )
            exit()
         turn_cards.append( new_pc )

      player1.hand, decks, player1.group_list, discard_pc = play_turn_new_cards( turn_cards, decks, rng, player1, verb_level=1 )
      ncnig1, ncnig_nwc1 = get_ncards_not_in_group( player1.hand, player1.group_list )
      print('  hand 1:    %d cards,     %d cards not in groups,        %d non-wildcards not in groups' % (len(player1.hand), ncnig1, ncnig_nwc1) )

      if discard_pc == 0 :
         print('\n\n *** no discard! ***  \n\n')

      if ncnig1 == 0 :
         if player1.down :
            print('\n\n ======= player 1 closed out!\n\n')
            player1.print_state()
            print('\n\n\n')
            player2.print_state()
            print('\n\n\n')
            exit()
         print('\n ---- turn %d, player 1, going down!\n\n' % ti )
         for gr in player1.group_list :
            still_in_hand = False
            board_group = group( gr.cards, gr.is_a_run, still_in_hand )
            player1.board_groups.append( board_group )
         player1.group_list = []
         player1.down = True
         player1.hand = decks[-11:]
         decks = decks[:-11]
         player1.hand.sort()
         player1.print_state()
         if discard_pc == 0 :
            print('\n No discard so still playing this turn...\n')

            player1.hand, decks, player1.group_list, discard_pc = play_turn_new_cards( turn_cards, decks, rng, player1, verb_level=1 )
            ncnig1, ncnig_nwc1 = get_ncards_not_in_group( player1.hand, player1.group_list )

            if ncnig1 == 0 :
               print('\n\n ======= player 1 closed out!\n\n')
               player1.print_state()
               print('\n\n\n')
               player2.print_state()
               print('\n\n\n')
               exit()

         batch = False


      pile.append( discard_pc )

      print('\n --- pile after player 1: ', end='' )
      print( pile )

      check_all_cards( player1, player2, decks, pile, verb_level=1 )

      if not batch :
         answ = input(' pausing...')
         if answ == 'q' : exit()
         if answ == 'c' : batch = True




      print('\n\n\n ===================================== turn %2d for player %s ====================================================================\n\n' % (ti, player2.name) )

      player2.print_state()

      pickup_pile = evaluate_pile( pile, decks, player2, verb_level=1 )

      ncnig2, ncnig_nwc2 = get_ncards_not_in_group( player2.hand, player2.group_list )

      turn_cards = []
      if pickup_pile  :
         print(' ***** picking up the pile ', end='' )
         print( pile )
         turn_cards.extend( pile )
         pile = []
      else :
         new_pc, decks = get_card_from_deck( decks )
         print(' card from deck: %d' % new_pc  )
         if new_pc == 0 :
            print('\n\n ======== no more cards!\n\n' )
            exit()
         turn_cards.append( new_pc )

      player2.hand, decks, player2.group_list, discard_pc = play_turn_new_cards( turn_cards, decks, rng, player2, verb_level=1 )
      ncnig2, ncnig_nwc2 = get_ncards_not_in_group( player2.hand, player2.group_list )
      print('  hand 2:    %d cards,     %d cards not in groups,        %d non-wildcards not in groups' % (len(player2.hand), ncnig2, ncnig_nwc2) )

      if discard_pc == 0 :
         print('\n\n *** no discard! ***\n\n')

      if ncnig2 == 0 :
         if player2.down :
            print('\n\n ======= player 2 closed out!\n\n')
            player2.print_state()
            print('\n\n\n')
            player1.print_state()
            print('\n\n\n')
            exit()
         print('\n ---- turn %d, player 2, going down!\n\n' % ti )
         for gr in player2.group_list :
            still_in_hand = False
            board_group = group( gr.cards, gr.is_a_run, still_in_hand )
            player2.board_groups.append( board_group )
         player2.group_list = []
         player2.down = True
         player2.hand = decks[-11:]
         decks = decks[:-11]
         player2.hand.sort()
         player2.print_state()
         if discard_pc == 0 :
            print('\n No discard so still playing this turn...\n')

            player2.hand, decks, player2.group_list, discard_pc = play_turn_new_cards( turn_cards, decks, rng, player2, verb_level=1 )
            ncnig2, ncnig_nwc2 = get_ncards_not_in_group( player2.hand, player2.group_list )

            if ncnig2 == 0 :
               print('\n\n ======= player 2 closed out!\n\n')
               player2.print_state()
               print('\n\n\n')
               player1.print_state()
               print('\n\n\n')
               exit()

         batch = False

      pile.append( discard_pc )

      print('\n --- pile after player 2: ', end='' )
      print( pile )

      check_all_cards( player1, player2, decks, pile, verb_level=1 )

      if not batch :
         answ = input(' pausing...')
         if answ == 'q' : exit()
         if answ == 'c' : batch = True


   print('\n\n')
   exit()




