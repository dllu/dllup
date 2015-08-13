" Vim syntax file
" Based on vim syntax file for Markdown by Tim Pope
" Language:     dllup
" Maintainer:   Daniel L. Lu dllu@dllu.net
" Filenames:    *.dllup *.dllu
" Last Change:  2015 Mar 12

if exists("b:current_syntax")
  finish
endif

if !exists('main_syntax')
  let main_syntax = 'dllup'
endif

runtime! syntax/html.vim
unlet! b:current_syntax

if !exists('g:dllup_fenced_languages')
  let g:dllup_fenced_languages = []
endif
for s:type in map(copy(g:dllup_fenced_languages),'matchstr(v:val,"[^=]*$")')
  if s:type =~ '\.'
    let b:{matchstr(s:type,'[^.]*')}_subtype = matchstr(s:type,'\.\zs.*')
  endif
  exe 'syn include @dllupHighlight'.substitute(s:type,'\.','','g').' syntax/'.matchstr(s:type,'[^.]*').'.vim'
  unlet! b:current_syntax
endfor
unlet! s:type

syn sync minlines=10
syn case ignore

syn match dllupValid '[<>]\c[a-z/$!]\@!'
syn match dllupValid '&\%(#\=\w*;\)\@!'

syn match dllupLineStart "^[<@]\@!" nextgroup=@dllupBlock,htmlSpecialChar

syn cluster dllupBlock contains=dllupH1,dllupH2,dllupH3,dllupH4,dllupH5,dllupH6,dllupBlockquote,dllupListMarker,dllupOrderedListMarker,dllupCodeBlock,dllupRule,dllupDisplayMath,dllupPic
syn cluster dllupInline contains=dllupLineBreak,dllupLinkText,dllupItalic,dllupBold,dllupCode,dllupEscape,@htmlTop,dllupError,dllupInlineMath,dllupCite,dllupRef

syn region dllupH1 matchgroup=dllupHeadingDelimiter start="##\@!"      end="#*\s*$" keepend oneline contains=@dllupInline,dllupAutomaticLink contained
syn region dllupH2 matchgroup=dllupHeadingDelimiter start="###\@!"     end="#*\s*$" keepend oneline contains=@dllupInline,dllupAutomaticLink contained
syn region dllupH3 matchgroup=dllupHeadingDelimiter start="####\@!"    end="#*\s*$" keepend oneline contains=@dllupInline,dllupAutomaticLink contained
syn region dllupH4 matchgroup=dllupHeadingDelimiter start="#####\@!"   end="#*\s*$" keepend oneline contains=@dllupInline,dllupAutomaticLink contained
syn region dllupH5 matchgroup=dllupHeadingDelimiter start="######\@!"  end="#*\s*$" keepend oneline contains=@dllupInline,dllupAutomaticLink contained
syn region dllupH6 matchgroup=dllupHeadingDelimiter start="#######\@!" end="#*\s*$" keepend oneline contains=@dllupInline,dllupAutomaticLink contained

syn region dllupCodeBlock start="^\~\~\~\~$" end="^\~\~\~\~$" contained
syn region dllupCodeBlock start="^\~\~\~$" end="^\~\~\~$" contained

syn region dllupBlockquote start="^> " end="\n\n" contains=@dllupInline contained
syn region dllupDisplayMath start="^\$ " end="\n\n" contained
syn region dllupPic start="^pic " end="\n\n" contains=@dllupInline,dllupAutomaticLink contained

" TODO: real nesting
syn match dllupListMarker "\%(\t\| \{0,4\}\)[*]\+\%(\s\+\S\)\@=" contained
syn match dllupOrderedListMarker "\%(\t\| \{0,4}\)\<\d\+\.\%(\s\+\S\)\@=" contained

syn match dllupRule "\* *\* *\*[ *]*$" contained
syn match dllupRule "- *- *-[ -]*$" contained

syn match dllupLineBreak " \{2,\}$"

syn region dllupIdDeclaration matchgroup=dllupLinkDelimiter start="^ \{0,3\}!\=\[" end="\]:" oneline keepend nextgroup=dllupUrl skipwhite
syn match dllupUrl "\S\+" nextgroup=dllupUrlTitle skipwhite contained
syn region dllupUrl matchgroup=dllupUrlDelimiter start="<" end=">" oneline keepend nextgroup=dllupUrlTitle skipwhite contained
syn region dllupUrlTitle matchgroup=dllupUrlTitleDelimiter start=+"+ end=+"+ keepend contained
syn region dllupUrlTitle matchgroup=dllupUrlTitleDelimiter start=+'+ end=+'+ keepend contained
syn region dllupUrlTitle matchgroup=dllupUrlTitleDelimiter start=+(+ end=+)+ keepend contained

syn region dllupLinkText matchgroup=dllupLinkTextDelimiter start="!\=\[\%(\_[^]]*]\%( \=[[(]\)\)\@=" end="\]\%( \=[[(]\)\@=" keepend nextgroup=dllupLink,dllupId skipwhite contains=@dllupInline,dllupLineStart
syn region dllupLink matchgroup=dllupLinkDelimiter start="(" end=")" contains=dllupUrl keepend contained
syn region dllupId matchgroup=dllupIdDelimiter start="\[" end="\]" keepend contained
syn region dllupAutomaticLink matchgroup=dllupUrlDelimiter start="<\%(\w\+:\|[[:alnum:]_+-]\+@\)\@=" end=">" keepend oneline

syn region dllupCite start="(#" end=")" keepend oneline contains=dllupLineStart
syn region dllupRef start="\[#" end="\]" keepend oneline contains=dllupLineStart

syn region dllupInlineMath start="\$" end="\$" keepend oneline contains=dllupLineStart
syn region dllupItalic start="\S\@<=_\|_\S\@=" end="\S\@<=_\|_\S\@=" keepend oneline contains=dllupLineStart
syn region dllupBold start="\S\@<=\*\*\|\*\*\S\@=" end="\S\@<=\*\*\|\*\*\S\@=" keepend oneline contains=dllupLineStart,dllupItalic
syn region dllupCode matchgroup=dllupCodeDelimiter start="[^\\]`" end="`" keepend contains=dllupLineStart

if main_syntax ==# 'dllup'
  for s:type in g:dllup_fenced_languages
    exe 'syn region dllupHighlight'.substitute(matchstr(s:type,'[^=]*$'),'\..*','','').' matchgroup=dllupCodeDelimiter start="^\s*```'.matchstr(s:type,'[^=]*').'\>.*$" end="^\s*```\ze\s*$" keepend contains=@dllupHighlight'.substitute(matchstr(s:type,'[^=]*$'),'\.','','g')
  endfor
  unlet! s:type
endif

syn match dllupEscape "\\[][\\`*_{}()#+.!-]"

hi def link dllupH1                    htmlH1
hi def link dllupH2                    htmlH2
hi def link dllupH3                    htmlH3
hi def link dllupH4                    htmlH4
hi def link dllupH5                    htmlH5
hi def link dllupH6                    htmlH6
hi def link dllupHeadingRule           dllupRule
hi def link dllupHeadingDelimiter      Delimiter
hi def link dllupOrderedListMarker     dllupListMarker
hi def link dllupListMarker            htmlTagName
hi def link dllupBlockquote            String
hi def link dllupPic                   Label
hi def link dllupRule                  PreProc
hi def link dllupInlineMath            dllupDisplayMath
hi def dllupDisplayMath           term=italic cterm=italic gui=italic ctermfg=blue guifg=blue
hi def link dllupCodeBlock             Comment

hi def link dllupLinkText              htmlLink
hi def link dllupIdDeclaration         Typedef
hi def link dllupId                    Type
hi def link dllupAutomaticLink         dllupUrl
hi def link dllupUrl                   Float
hi def link dllupUrlTitle              String
hi def link dllupRef                   htmlTagName
hi def link dllupCite                  htmlTagName
hi def link dllupCode                  Comment
hi def link dllupIdDelimiter           dllupLinkDelimiter
hi def link dllupUrlDelimiter          htmlTag
hi def link dllupUrlTitleDelimiter     Delimiter

hi def link dllupItalic                htmlItalic
hi def link dllupBold                  htmlBold
hi def link dllupCodeDelimiter         Delimiter

hi def link dllupEscape                Special
hi def link dllupError                 Error

let b:current_syntax = "dllup"
if main_syntax ==# 'dllup'
  unlet main_syntax
endif

" vim:set sw=2:
