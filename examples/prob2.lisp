(
    ( defvar a 1 )
    ( defvar b 1 )
    ( defvar tmp 0 )
    ( defvar sum 0 )
    (
        while ( < b 4000000 )
        (
            ( setq tmp b )
            ( setq b ( + a b ) )
            ( setq a tmp )
            ( if ( = ( mod b 2 ) 0 )
                (
                    setq sum ( + sum b )
                )
            )
        )
    )
    ( print sum )
)