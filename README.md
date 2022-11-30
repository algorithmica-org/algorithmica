# Algorithmica v3

Algorithmica is an open-access web book dedicated to the art and science of computing.

You can contribute via [Prose](https://prose.io/) by clicking on the pencil icon on the top right on any page or by editing its source directly on GitHub. We use a slightly different Markdown dialect, so if you are not sure that the change is correct (for example, editing an intricate LaTeX formula), you can install [Hugo](https://gohugo.io/) and build the site locally — or just create a pull request, and a preview link will be automatically generated for you.

If you happen to speak Russian, please also read the [contributing guidelines](https://ru.algorithmica.org/contributing/).

---

Key technical changes from the [previous version](https://github.com/algorithmica-org/articles):

* pandoc -> Hugo
* CSS -> Sass
* Github Pages -> Netlify
* Yandex.Metrica -> ~~Google Analytics~~ went back to Metrica
* algorithmica.org/{lang}/* -> {lang}.algorithmica.org/*
* Rich metadata support (language, sections, TOCs, authors...)
* Automated global table of contents
* Theming support
* Search support (Lunr)

Short-term todo list:

* Style adjustments for mobile and print versions
* A pdf version of the whole website
* Meta-information support (for Google Scholar and social media)
* [Sticky table of contents](https://css-tricks.com/table-of-contents-with-intersectionobserver/)
