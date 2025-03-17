#include "globals.h"
#include <QString>
#include <windows.h>

#ifdef _WIN32
const char *get_locale(void) {
  static wchar_t localeStr[128];
  LCID locale = GetUserDefaultLCID();

  int langLen = GetLocaleInfo(locale, LOCALE_SISO639LANGNAME, localeStr,
                              sizeof(localeStr) / sizeof(wchar_t));

  if (langLen > 0) {
    wchar_t country[128];
    int countryLen = GetLocaleInfo(locale, LOCALE_SISO3166CTRYNAME, country,
                                   sizeof(country) / sizeof(wchar_t));

    if (countryLen > 0) {
      wcscat(localeStr, L" - ");
      wcscat(localeStr, country);
      static char result[128];
      wcstombs(result, localeStr, sizeof(result));
      return result;
    } else {
      static char result[128];
      wcstombs(result, localeStr, sizeof(result));
      return result;
    }
  } else {
    return "Locale info could not be retrieved.";
  }
}

#elif __linux__
const char *get_locale(void) {
  const char *currentLocale = setlocale(LC_ALL, NULL); // Linux
  if (currentLocale != NULL) {
    return currentLocale;
  } else {
    return "Locale could not be retrieved.";
  }
}
#endif

const char *get_language_by_lcid(const QString &lcid) {
  if (languages.contains(lcid)) {
    return languages.value(lcid).toUtf8().constData();
  }
  return "Unknown Language";
}
