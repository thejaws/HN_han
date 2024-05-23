use autodie;

print(">> " . $ARGV[0]. "\n");
my $infile  = $ARGV[0];
my $outfile = $infile . "_decoded.txt";
open my $ofh, '>', $outfile;
open my $fh, '<:raw', $infile;
my $i;
while (my $bytes_read = read $fh, my $bytes, 1) {
	$i++;
	die "Got $bytes_read but expected 44" unless $bytes_read == 1;
	print $ofh unpack("H*" , $bytes). " ";
	if ($i % 40 == 0){
		print $ofh "\n";
	}
}
close $ofh;
close $fh;
