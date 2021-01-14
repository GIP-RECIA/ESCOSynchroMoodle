#!/usr/bin/perl

=encoding utf8


=pod

Script qui permet pour supprimer les doublons sur les cohortes qui faisait planter les synchro
doublons => cohorte avec le meme nom et meme contextid , le reste differt

le principe quand il y a un doublon on supprime la cohort qui n'a pas de cours associé

=cut

use strict;
use utf8;
use open qw( :encoding(utf8) :std );
use Unicode::Normalize;

use DBI();

my $config=do("./config.pl");
die "Error parsing config file: $@" if $@;
die "Error reading config file: $!" unless defined $config;

my $sqlHost = $config->{sqlHost};
my $sqlDatabase = $config->{sqlDatabase};
my $sqlUsr = $config->{sqlUsr};
my $sqlPass = $config->{sqlPass};
my $sqlPort = $config->{sqlPort};
my $sqlDataSource = "DBI:mysql:database=$sqlDatabase;host=$sqlHost;port=$sqlPort";
my $SQL_CONNEXION;

sub connectSql {
	if ($SQL_CONNEXION) {
		return $SQL_CONNEXION;
	}
	print "connexion sql: $sqlDataSource, $sqlUsr, ...:\n";
	$SQL_CONNEXION = DBI->connect($sqlDataSource, $sqlUsr, $sqlPass) || die $!;
	print " OK \n";
	$SQL_CONNEXION->{'mysql_auto_reconnect'} = 1;
	$SQL_CONNEXION->{'mysql_enable_utf8'} = 1;
	$SQL_CONNEXION->do('SET NAMES utf8');
	return $SQL_CONNEXION ;
}

my $sql = connectSql();

# recherche des doublons : 
my $sqlQuery = "select contextid, name , count(id) from mdl_cohort group by contextid, name having count(id) > 1";

my $sqlStatement = $sql->prepare($sqlQuery) or die $sql->errstr;

$sqlStatement->execute() or die $sqlStatement->errstr;

my $queryDouble =  "select *, (select count(cm1.userid) from mdl_cohort_members cm1 where cm1.cohortid= c.id) nbUser , 
(select count(courseid) from mdl_enrol where enrol = 'cohort' and customint1 =c.id) nbCours from mdl_cohort c where contextid = ? and name = ?";
my $statementDouble = $sql->prepare($queryDouble) or die $sql->errstr;

while (my $tuple =  $sqlStatement->fetchrow_hashref()) {
	&traitementDoublon($tuple->{'contextid'}, $tuple->{'name'},  $statementDouble );
}

sub traitementDoublon(){
	my $contextId = shift;
	my $cName = shift;
	my $statement = shift;
	
	$statement->execute($contextId, $cName);
	my @couple;
	my $idKo = 0;
	my $estVide = 0;
	my $nbVide = 0;
	my $cpt=0;
	
	while (my $tuple =  $statement->fetchrow_hashref()) {
		$couple[$cpt] = $tuple;
		my $cohortId = $tuple->{'id'};
		my $idNumber =  $tuple->{'idnumber'} ;
		my $nbUser = $tuple->{'nbUser'};
		my $nbCours = $tuple->{'nbCours'};
		if ($idNumber ne $cName) {
			 $idKo = $cpt;
		} else {
			$tuple->{'idOk'} = 1;
		}
		if ($nbUser + $nbCours == 0) {
			$nbVide++;
			$tuple->{'estVide'} = 1;
			$estVide = $cpt;
		}
		
		print "$cohortId $contextId; $cName; ", $tuple->{'idnumber'} , "; ", $tuple->{'nbUser'} ,"; ", $tuple->{'nbCours'} , , "\n";
		$cpt++;
	}
	if ($cpt == 2){
		if ($nbVide == 2) {
				# si les 2 sont vide on delete celui avec le mauvais idNumber
			&deleteCohorte($couple[$idKo]);
		} elsif ($nbVide == 1) {
				# si un seul on le delete
			&deleteCohorte($couple[$estVide]);
			if ($estVide != $idKo) {
				&updateCohorte($couple[$idKo], $couple[$estVide]->{'idnumber'} , $couple[$estVide]->{'description'});
			}
			
		} else {
			# cas plus dificile ou il des membres ou des classes.
				
				my $count0 = $couple[0]->{'nbCours'};
				my $count1 = $couple[1]->{'nbCours'};
				if ($count0 == $count1) {
					if ($count0) {
						print "les deux ont des cours\n";
						if (&memeCours($couple[0]->{'id'}, $couple[1]->{'id'}) ){
								print ("meme liste de cours\n");
								unless ($couple[$idKo]->{'idOk'}){
									&deleteCohorte($couple[$idKo]);
								}
						} else {
							print "liste des cours differenes \n";
						}
					} else {
						unless ($couple[$idKo]->{'idOk'}){
							&deleteCohorte($couple[$idKo]);
						}
					}
				} else {
					print "nombres de cours differents"; 
				}
				
		} 
	}else {
		print "mauvais compte \n";
	}		
}

sub keepFirst(){
	my $aGarder = shift;
	my $aSupprimer = shift;
	print "supprimer " ,  $aSupprimer->{'id'};
}

sub memeCours {
	my $setCours1 = setIdCours(shift);
	my $setCours2 = setIdCours(shift);
	foreach my $cours (keys %$setCours1) {
		unless ($setCours2->{$cours}) {
			return 0;
		}
	}
	return 1;
}

sub setIdCours{
	my $idCohort = shift;
	my $query =	"select courseid from mdl_enrol where enrol = 'cohort' and customint1 = ? ";
	my $statement = connectSql()->prepare($query) or die $sql->errstr;
	$statement->execute($idCohort);
	my %res;
	while (my $tuple =  $statement->fetchrow_hashref()) {
		$res{$tuple->{'courseid'}} = 1;
		print $tuple->{'courseid'}, " ";
	}
	print "\n";
	return \%res;
}

sub updateCohorte {
	my $cohorte = shift;
	my $query = "update  mdl_cohort set idnumber = ? , description = ? where id= ?";
	print "$query ;" , $cohorte->{'idnumber'}, $cohorte->{'description'},  $cohorte->{'id'}, ' ... ';
	my $count = connectSql()->do($query, undef, $cohorte->{'idnumber'}, $cohorte->{'description'} , $cohorte->{'id'});
	print "$count \n"; 
}
sub deleteCohorte {
	my $cohorte = shift;
	my $query = "delete from mdl_cohort where id = ?" ;
	print "$query ;" , $cohorte->{'id'} , ' ... ';
	my $count = connectSql()->do($query, undef, $cohorte->{'id'});
	print "$count \n"; 
	if ($cohorte->{'nbUser'} > 0 ) {
		$query = "delete from mdl_cohort_members where cohortid = ?" ;
		$count = connectSql()->do($query, undef, $cohorte->{'id'});
		print "delete member => $count / ", $cohorte->{'nbUser'}," \n"; 
	}
	if ($cohorte->{'nbCours'} > 0 ) {
		 $query = "delete from mdl_enrol where enrol = 'cohort' and customint1 = ? '";
		 $count = connectSql()->do($query, undef, $cohorte->{'id'});
		 print "delete enrol  => $count / ", $cohorte->{'nbCours'}," \n"; 
	}
	
}

