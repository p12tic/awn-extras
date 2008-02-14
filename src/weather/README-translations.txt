
Instructions for providing new language files
=============================================

Would you like to translate the AWN Weather Applet to your native
language?  If you speak more than one language, it's an easy way
to contribute to Open Source!  Here's what you need to do:

1.) In the weather directory, run the msginit command, and specify
    the locale code on the command line.  For example, to translate
    to French, you'd do
    
    			msginit --locale=fr
    
    This will run an interactive utility which will generate a .po file
    for you.

2.) Edit the .po file.  The .po file contains a bunch of English strings
    (or msgid's), followed by their translation (msgstr's).  Your job
    is to fill in the msgstr's between the quotes.  One other thing to
    make sure of: at approximately line 13 is a line that looks something
    like this:
    
    "Content-Type: text/plain; charset=UTF-8\n"
    
    make sure the charset is UTF-8, *not* ASCII.  ASCII will almost certainly
    not work.  You can check the weather/po/es.po file for an example of
    a working po file.

If you're not feeling adventurous, you can stop here.  E-mail your .po file
to desjardinsmike@gmail.com, and I'll try to get your translation into the
next build.  If you'd actually like to see immediate results for your hard 
work, then read on...

3.) Next, you need to compile your .po file into an .mo file.  To do this,
    you should use the Python msgfmt.py script.  If you use Ubuntu, you can
    get a copy in the python-examples package.  For some reason, it gets 
    installed in /usr/share/doc/python2.4/examples/Tools/i18n/msgfmt.py
    on Ubuntu.   Run this script, and supply the .po filename as the input
    parameter.  It should output a similarly named file with the .mo extension

4.) Create a directory in the weather/locale directory named for your locale.
    For example, the Japanese jp locale would be in weather/locale/jp.  In that
    directory, create another directory called LC_MESSAGES.

5.) Rename your .mo file to awn-weather-applet.mo, and put it into the newly 
    created LC_MESSAGES directory.

Restart the applet and check the results!

For more help, the "One Laptop Per Child" (OLPC) project has created a Wiki
page for translating their Python applications; you might find it to be
useful.  You can find that Wiki here:

http://wiki.laptop.org/go/Python_i18n

Good luck!

- Mike (a.k.a. Mosburger)

    
    