%define _hardened_build 1
%global selinux_variants mls strict targeted

Name:		monetaryunit
Version:	1.0.0.1
Release:	2%{?dist}
Summary:	Peer-to-peer digital currency

Group:		Applications/System
License:	MIT
URL:		http://monetaryunit.org/
Source0:	https://github.com/MonetaryUnit/MUE-Src/archive/1.0.0.1.tar.gz
Source2:	monetaryunit.service
Source3:	monetaryunit.init
Source4:	monetaryunit.te
Source5:	monetaryunit.fc
Source6:	monetaryunit.if
Source7:	README.server.redhat
Source8:	README.cli.redhat
Source9:	README.gui.redhat

BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	qt5-devel qrencode-devel openssl-devel miniupnpc-devel protobuf-devel
BuildRequires:	desktop-file-utils autoconf automake
BuildRequires:	checkpolicy, selinux-policy-devel, /usr/share/selinux/devel/policyhelp

%if 0%{?rhel} >= 7 || 0%{?fedora}
BuildRequires:	boost-devel libdb4-cxx-devel
%else
BuildRequires:	boost-devel db4-devel
%endif

Requires:	openssl >= 1.0.1i


%package cli
Summary:	Peer-to-peer digital currency
Requires:	openssl >= 1.0.1i


%package server
Summary:	Peer-to-peer digital currency
%if 0%{?rhel} >= 7 || 0%{?fedora} >= 21
Requires(post):	systemd
Requires(preun):	systemd
Requires(postun):	systemd
BuildRequires:	systemd
%else
Requires(post):	chkconfig
Requires(preun):	chkconfig
# This is for /sbin/service
Requires(preun):	initscripts
Requires(postun):	initscripts
%endif
Requires(pre):	shadow-utils
Requires(post):	/usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles
Requires(postun):	/usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles
Requires:	selinux-policy
Requires:	policycoreutils-python
Requires:	openssl >= 1.0.1i
Requires:	monetaryunit-cli%{_isa} = %{version}


%description
MonetaryUnit is an experimental new digital currency that enables instant
payments to anyone, anywhere in the world. MonetaryUnit uses peer-to-peer
technology to operate with no central authority: managing transactions
and issuing money are carried out collectively by the network.

MonetaryUnit is also the name of the open source software which enables the
use of this currency.

This package provides MonetaryUnit-QT, a user-friendly wallet manager for
personal use.


%description cli
MonetaryUnit is an experimental new digital currency that enables instant
payments to anyone, anywhere in the world. MonetaryUnit uses peer-to-peer
technology to operate with no central authority: managing transactions
and issuing money are carried out collectively by the network.

This package provides monetaryunit-cli, a utility to communicate with and
control a MonetaryUnit server via its RPC protocol.


%description server
MonetaryUnit is an experimental new digital currency that enables instant
payments to anyone, anywhere in the world. MonetaryUnit uses peer-to-peer
technology to operate with no central authority: managing transactions
and issuing money are carried out collectively by the network.

This package provides monetaryunitd, a wallet server.


%prep
%setup -q -n %{name}-%{version}

# Install README files
cp -p %{SOURCE7} %{SOURCE8} %{SOURCE9} .

# Prep SELinux policy
mkdir SELinux
cp -p %{SOURCE4} %{SOURCE5} %{SOURCE6} SELinux


%build
# Build MonetaryUnit
./autogen.sh
%if 0%{?rhel} >= 7 || 0%{?fedora}
%configure --with-incompatible-bdb \
	PKG_CONFIG_PATH=/opt/openssl-compat-monetaryunit/lib/pkgconfig \
	LIBS=-Wl,-rpath,/opt/openssl-compat-monetaryunit/lib
%else
%ifarch x86_64
%configure --with-incompatible-bdb \
	--with-boost=/opt/boost-compat-monetaryunit \
	PKG_CONFIG_PATH=/opt/openssl-compat-monetaryunit/lib/pkgconfig \
	LIBS=-Wl,-rpath,/opt/openssl-compat-monetaryunit/lib,-rpath,/opt/boost-compat-monetaryunit/lib64
%else
%configure --with-incompatible-bdb \
	--with-boost=/opt/boost-compat-monetaryunit \
	PKG_CONFIG_PATH=/opt/openssl-compat-monetaryunit/lib/pkgconfig \
	LIBS=-Wl,-rpath,/opt/openssl-compat-monetaryunit/lib,-rpath,/opt/boost-compat-monetaryunit/lib
%endif
%endif

# TODO: Building currently fails intermittently when parallelized :(
make %{?_smp_mflags}
#make

# Build SELinux policy
pushd SELinux
for selinuxvariant in %{selinux_variants}
do
# FIXME: Create and debug SELinux policy
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
  mv monetaryunit.pp monetaryunit.pp.${selinuxvariant}
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
popd


%install
rm -rf %{buildroot}
mkdir %{buildroot}
cp contrib/debian/examples/monetaryunit.conf monetaryunit.conf.example

make INSTALL="install -p" CP="cp -p" DESTDIR=%{buildroot} install

# TODO: Upstream puts monetaryunitd in the wrong directory. Need to fix the
# upstream Makefiles to relocate it.
mkdir -p -m 755 %{buildroot}%{_sbindir}
mv %{buildroot}%{_bindir}/monetaryunitd %{buildroot}%{_sbindir}/monetaryunitd

# Install ancillary files
mkdir -p -m 755 %{buildroot}%{_datadir}/pixmaps
install -D -m644 -p share/pixmaps/monetaryunit*.{png,xpm,ico} %{buildroot}%{_datadir}/pixmaps/
install -D -m644 -p contrib/debian/monetaryunit-qt.desktop %{buildroot}%{_datadir}/applications/monetaryunit-qt.desktop
desktop-file-validate %{buildroot}%{_datadir}/applications/monetaryunit-qt.desktop
install -D -m644 -p contrib/debian/monetaryunit-qt.protocol %{buildroot}%{_datadir}/kde4/services/monetaryunit-qt.protocol
%if 0%{?rhel} >= 7 || 0%{?fedora} >= 21
install -D -m644 -p %{SOURCE2} %{buildroot}%{_unitdir}/monetaryunit.service
%else
install -D -m755 -p %{SOURCE3} %{buildroot}%{_initrddir}/monetaryunit
%endif
install -d -m750 -p %{buildroot}%{_localstatedir}/lib/monetaryunit
install -d -m750 -p %{buildroot}%{_sysconfdir}/monetaryunit
install -D -m644 -p contrib/debian/manpages/monetaryunitd.1 %{buildroot}%{_mandir}/man1/monetaryunitd.1
install -D -m644 -p contrib/debian/manpages/monetaryunit-qt.1 %{buildroot}%{_mandir}/man1/monetaryunit-qt.1
install -D -m644 -p contrib/debian/manpages/monetaryunit.conf.5 %{buildroot}%{_mandir}/man5/monetaryunit.conf.5
gzip %{buildroot}%{_mandir}/man1/monetaryunitd.1
gzip %{buildroot}%{_mandir}/man1/monetaryunit-qt.1
gzip %{buildroot}%{_mandir}/man5/monetaryunit.conf.5

# Remove test files
rm -f %{buildroot}%{_bindir}/test_*

# Install SELinux policy
for selinuxvariant in %{selinux_variants}
do
	install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
	install -p -m 644 SELinux/monetaryunit.pp.${selinuxvariant} \
		%{buildroot}%{_datadir}/selinux/${selinuxvariant}/monetaryunit.pp
done


%clean
rm -rf %{buildroot}


%pre server
getent group monetaryunit >/dev/null || groupadd -r monetaryunit
getent passwd monetaryunit >/dev/null ||
	useradd -r -g monetaryunit -d /var/lib/monetaryunit -s /sbin/nologin \
	-c "MonetaryUnit wallet server" monetaryunit
exit 0


%post server
%if 0%{?rhel} >= 7 || 0%{?fedora} >= 21
%systemd_post monetaryunit.service
%else
/sbin/chkconfig --add monetaryunit
%endif
for selinuxvariant in %{selinux_variants}
do
	/usr/sbin/semodule -s ${selinuxvariant} -i \
		%{_datadir}/selinux/${selinuxvariant}/monetaryunit.pp \
		&> /dev/null || :
done
# FIXME This is less than ideal, but until dwalsh gives me a better way...
/usr/sbin/semanage port -a -t monetaryunit_port_t -p tcp 29947
/usr/sbin/semanage port -a -t monetaryunit_port_t -p tcp 29948
/usr/sbin/semanage port -a -t monetaryunit_port_t -p tcp 39947
/usr/sbin/semanage port -a -t monetaryunit_port_t -p tcp 39948
/sbin/fixfiles -R monetaryunit-server restore &> /dev/null || :
/sbin/restorecon -R %{_localstatedir}/lib/monetaryunit || :


%preun server
%if 0%{?rhel} >= 7 || 0%{?fedora} >= 21
%systemd_preun monetaryunit.service
%else
if [ $1 -eq 0 ] ; then
    /sbin/service monetaryunit stop >/dev/null 2>&1
    /sbin/chkconfig --del monetaryunit
fi
%endif


%postun server
%if 0%{?rhel} >= 7 || 0%{?fedora} >= 21
%systemd_postun monetaryunit.service
%else
if [ "$1" -ge "1" ] ; then
	/sbin/service monetaryunit condrestart >/dev/null 2>&1 || :
fi
%endif
if [ $1 -eq 0 ] ; then
	# FIXME This is less than ideal, but until dwalsh gives me a better way...
	/usr/sbin/semanage port -d -p tcp 8332
	/usr/sbin/semanage port -d -p tcp 8333
	/usr/sbin/semanage port -d -p tcp 18332
	/usr/sbin/semanage port -d -p tcp 18333
	for selinuxvariant in %{selinux_variants}
	do
		/usr/sbin/semodule -s ${selinuxvariant} -r monetaryunit \
		&> /dev/null || :
	done
	/sbin/fixfiles -R monetaryunit-server restore &> /dev/null || :
	[ -d %{_localstatedir}/lib/monetaryunit ] && \
		/sbin/restorecon -R %{_localstatedir}/lib/monetaryunit \
		&> /dev/null || :
fi


%files
%defattr(-,root,root,-)
%doc COPYING README.md README.gui.redhat doc/tor.md monetaryunit.conf.example
%{_bindir}/monetaryunit-qt
%{_datadir}/applications/monetaryunit-qt.desktop
%{_datadir}/kde4/services/monetaryunit-qt.protocol
%{_datadir}/pixmaps/*
%{_mandir}/man1/monetaryunit-qt.1.gz


%files cli
%defattr(-,root,root,-)
%doc COPYING README.md README.cli.redhat monetaryunit.conf.example
%{_bindir}/monetaryunit-cli


%files server
%defattr(-,root,root,-)
%doc COPYING README.md README.server.redhat doc/tor.md monetaryunit.conf.example
%dir %attr(750,monetaryunit,monetaryunit) %{_localstatedir}/lib/monetaryunit
%dir %attr(750,monetaryunit,monetaryunit) %{_sysconfdir}/monetaryunit
%doc SELinux/*
%{_sbindir}/monetaryunitd
%if 0%{?rhel} >= 7 || 0%{?fedora} >= 21
%{_unitdir}/monetaryunit.service
%else
%{_initrddir}/monetaryunit
%endif
%{_mandir}/man1/monetaryunitd.1.gz
%{_mandir}/man5/monetaryunit.conf.5.gz
%{_datadir}/selinux/*/monetaryunit.pp


%changelog
* Sat Apr 28 2015 upgradeadvice <upgradeadvice@gmail.com> 1.0.0.1
- Initial
