from os.path import join, dirname

from audiobooker.scrappers.librivox import Librivox
from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_utils.parse import fuzzy_match, MatchStrategy
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search, ocp_featured_media


class LibrivoxSkill(OVOSCommonPlaybackSkill):
    def __init__(self):
        super(LibrivoxSkill, self).__init__("Librivox")
        self.supported_media = [MediaType.GENERIC, MediaType.AUDIOBOOK]
        self.skill_icon = join(dirname(__file__), "ui", "librivox-logo.png")
        self.skill_bg = join(dirname(__file__), "ui", "bg.jpeg")
        self.skill_pic = join(dirname(__file__), "ui", "librivox-icon.png")

    def calc_score(self, phrase, match, idx=0, base_score=0):
        # idx represents the order from librivox
        score = base_score - idx  # - 1% as we go down the results list

        score += 100 * fuzzy_match(phrase.lower(), match.title.lower(),
                                   strategy=MatchStrategy.TOKEN_SET_RATIO)

        return min(100, score)

    # common play
    @ocp_featured_media()
    def featured_media(self):
        for book in Librivox.scrap_all_audiobooks(limit=50):
            yield self._book2ocp(book)

    @ocp_search()
    def search_librivox(self, phrase, media_type):
        # match the request media_type
        base_score = 0
        if media_type == MediaType.AUDIOBOOK:
            base_score += 25
        else:
            base_score -= 15

        if self.voc_match(phrase, "librivox"):
            # explicitly requested librivox
            base_score += 50
            phrase = self.remove_voc(phrase, "librivox")

        librivox = Librivox()
        results = librivox.search_audiobooks(title=phrase)
        if not results:  # hack: librivox search is not great...
            blacklist = ["the", "in", "on", "at"]
            phrase = " ".join([w for w in phrase.split(" ")
                               if w and w not in blacklist])
            results = librivox.search_audiobooks(title=phrase)

        for idx, book in enumerate(results):
            score = self.calc_score(phrase, book, idx=idx,
                                    base_score=base_score)
            yield self._book2ocp(book, score)

    def _book2ocp(self, book, score=50):
        author = " ".join([au.first_name + au.last_name for au in
                           book.authors])
        pl = [{
            "match_confidence": score,
            "media_type": MediaType.AUDIOBOOK,
            "uri": s,
            "artist": author,
            "playback": PlaybackType.AUDIO,
            "image": self.skill_pic,
            "bg_image": self.skill_bg,
            "skill_icon": self.skill_icon,
            "title": s.split("/")[-1].split(".")[0].replace("_", " "),
            "skill_id": self.skill_id
        } for ch, s in enumerate(book.streams)]

        return {
            "match_confidence": score,
            "media_type": MediaType.AUDIOBOOK,
            "playback": PlaybackType.AUDIO,
            "playlist": pl,  # return full playlist result
            "length": book.runtime * 1000,
            "image": self.skill_pic,
            "artist": author,
            "bg_image": self.skill_bg,
            "skill_icon": self.skill_icon,
            "title": book.title,
            "skill_id": self.skill_id
        }


def create_skill():
    return LibrivoxSkill()
